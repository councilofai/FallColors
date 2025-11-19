"""API routes for the Chatbot Testbed Platform."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
import asyncio
import logging

from app.core.database import get_db, TestSession as DBTestSession
from app.services.test_orchestrator import TestOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Store active test sessions
active_tests: Dict[str, TestOrchestrator] = {}


class StartTestRequest(BaseModel):
    """Request model for starting a test."""
    url: str
    topic: str
    max_rounds: Optional[int] = 10
    adversarial_intensity: Optional[int] = 5
    input_selector: Optional[str] = None
    submit_selector: Optional[str] = None
    headless: Optional[bool] = False


class TestSessionResponse(BaseModel):
    """Response model for test session."""
    session_id: str
    status: str
    url: str
    topic: str
    max_rounds: int
    adversarial_intensity: int


@router.post("/test/start", response_model=TestSessionResponse)
async def start_test(
    request: StartTestRequest,
    db: Session = Depends(get_db)
) -> TestSessionResponse:
    """
    Start a new chatbot test session.

    Args:
        request: Test configuration
        db: Database session

    Returns:
        Test session information
    """
    # Create database record
    db_session = DBTestSession(
        url=request.url,
        topic=request.topic,
        max_rounds=request.max_rounds,
        adversarial_intensity=request.adversarial_intensity,
        input_selector=request.input_selector,
        submit_selector=request.submit_selector,
        status="pending"
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    session_id = db_session.id

    logger.info(f"Created test session {session_id}")

    return TestSessionResponse(
        session_id=session_id,
        status="pending",
        url=request.url,
        topic=request.topic,
        max_rounds=request.max_rounds,
        adversarial_intensity=request.adversarial_intensity
    )


@router.post("/test/{session_id}/run")
async def run_test(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Run a test session.

    Args:
        session_id: Session ID to run
        db: Database session

    Returns:
        Status message
    """
    # Get session from database
    db_session = db.query(DBTestSession).filter(DBTestSession.id == session_id).first()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.status != "pending":
        raise HTTPException(status_code=400, detail="Session already started or completed")

    # Update status
    db_session.status = "running"
    db.commit()

    # Create event callback for WebSocket
    async def event_callback(event: Dict):
        """Send events to WebSocket if connected."""
        if session_id in active_connections:
            try:
                await active_connections[session_id].send_json(event)
            except Exception as e:
                logger.error(f"Error sending WebSocket event: {e}")

    # Create orchestrator
    orchestrator = TestOrchestrator(
        session_id=session_id,
        url=db_session.url,
        topic=db_session.topic,
        max_rounds=db_session.max_rounds,
        adversarial_intensity=db_session.adversarial_intensity,
        input_selector=db_session.input_selector,
        submit_selector=db_session.submit_selector,
        headless=db_session.input_selector is not None,  # Use headless if selectors provided
        event_callback=event_callback
    )

    active_tests[session_id] = orchestrator

    # Run test in background
    asyncio.create_task(run_test_background(session_id, orchestrator, db_session, db))

    return {"status": "started", "session_id": session_id}


async def run_test_background(
    session_id: str,
    orchestrator: TestOrchestrator,
    db_session: DBTestSession,
    db: Session
):
    """Run test in background and update database."""
    try:
        results = await orchestrator.run()

        # Update database with results
        db_session.status = results["status"]
        db_session.conversation = results.get("conversation", [])
        db_session.safety_scores = results.get("safety_evaluations", [])
        db_session.screenshots = results.get("screenshots", [])

        if "report" in results:
            db_session.overall_safety_score = results["report"]["summary"]["average_overall_score"]
            db_session.vulnerabilities_found = results["report"]["vulnerabilities"]
            db_session.recommendations = results["report"]["recommendations"]

        if "error" in results:
            db_session.error_message = results["error"]

        from datetime import datetime
        db_session.completed_at = datetime.utcnow()

        db.commit()

    except Exception as e:
        logger.error(f"Background test failed: {e}")
        db_session.status = "failed"
        db_session.error_message = str(e)
        db.commit()

    finally:
        # Cleanup
        if session_id in active_tests:
            del active_tests[session_id]


@router.get("/test/{session_id}")
async def get_test_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get test session details.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Session details
    """
    db_session = db.query(DBTestSession).filter(DBTestSession.id == session_id).first()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": db_session.id,
        "url": db_session.url,
        "topic": db_session.topic,
        "max_rounds": db_session.max_rounds,
        "adversarial_intensity": db_session.adversarial_intensity,
        "status": db_session.status,
        "started_at": db_session.started_at.isoformat() if db_session.started_at else None,
        "completed_at": db_session.completed_at.isoformat() if db_session.completed_at else None,
        "conversation": db_session.conversation,
        "safety_scores": db_session.safety_scores,
        "overall_safety_score": db_session.overall_safety_score,
        "vulnerabilities_found": db_session.vulnerabilities_found,
        "recommendations": db_session.recommendations,
        "error_message": db_session.error_message
    }


@router.get("/test")
async def list_test_sessions(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all test sessions.

    Args:
        limit: Maximum number of sessions to return
        db: Database session

    Returns:
        List of sessions
    """
    sessions = db.query(DBTestSession).order_by(
        DBTestSession.started_at.desc()
    ).limit(limit).all()

    return [
        {
            "session_id": s.id,
            "url": s.url,
            "topic": s.topic,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "overall_safety_score": s.overall_safety_score
        }
        for s in sessions
    ]


@router.delete("/test/{session_id}")
async def delete_test_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a test session.

    Args:
        session_id: Session ID
        db: Database session

    Returns:
        Status message
    """
    db_session = db.query(DBTestSession).filter(DBTestSession.id == session_id).first()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Stop active test if running
    if session_id in active_tests:
        await active_tests[session_id].stop()
        del active_tests[session_id]

    db.delete(db_session)
    db.commit()

    return {"status": "deleted", "session_id": session_id}


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time test updates.

    Args:
        websocket: WebSocket connection
        session_id: Session ID to subscribe to
    """
    await websocket.accept()
    active_connections[session_id] = websocket

    logger.info(f"WebSocket connected for session {session_id}")

    try:
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            logger.debug(f"Received WebSocket message: {data}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if session_id in active_connections:
            del active_connections[session_id]


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chatbot-testbed"}
