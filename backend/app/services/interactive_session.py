"""Interactive browser session service for manual testing."""

import asyncio
import sys
import logging
from typing import Dict, Optional
from app.services.browser_service import BrowserService

# Fix for Windows: Ensure event loop policy is set for Playwright
# This needs to be set before any Playwright operations
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except RuntimeError:
        # Policy already set, ignore
        pass

logger = logging.getLogger(__name__)

# Store active interactive sessions
interactive_sessions: Dict[str, BrowserService] = {}


async def create_interactive_session(session_id: str, url: str) -> Dict:
    """
    Create and start an interactive browser session.

    Args:
        session_id: Unique session identifier
        url: URL to navigate to

    Returns:
        Dictionary with session status
    """
    try:
        logger.info(f"Creating interactive session {session_id} for URL: {url}")

        # Create browser service (always non-headless for interactive mode)
        browser = BrowserService(headless=False)

        # Start browser
        await browser.start()
        logger.info(f"Browser started for session {session_id}")

        # Navigate to URL
        success = await browser.navigate(url)
        if not success:
            await browser.stop()
            return {
                "status": "error",
                "message": "Failed to navigate to URL"
            }

        logger.info(f"Successfully navigated to {url}")

        # Get page info
        page_info = await browser.get_page_info()

        # Take initial screenshot
        screenshot = await browser.take_screenshot()

        # Store the browser session
        interactive_sessions[session_id] = browser

        return {
            "status": "success",
            "session_id": session_id,
            "url": page_info["url"],
            "title": page_info["title"],
            "screenshot": screenshot,
            "message": "Browser session opened successfully. You can now interact with the page."
        }

    except Exception as e:
        logger.error(f"Error creating interactive session: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


async def get_session_screenshot(session_id: str) -> Optional[str]:
    """
    Get a screenshot from an active session.

    Args:
        session_id: Session identifier

    Returns:
        Base64 encoded screenshot or None
    """
    if session_id not in interactive_sessions:
        return None

    browser = interactive_sessions[session_id]
    return await browser.take_screenshot()


async def get_session_info(session_id: str) -> Optional[Dict]:
    """
    Get information about an active session.

    Args:
        session_id: Session identifier

    Returns:
        Session information or None
    """
    if session_id not in interactive_sessions:
        return None

    browser = interactive_sessions[session_id]
    page_info = await browser.get_page_info()
    screenshot = await browser.take_screenshot()

    return {
        "session_id": session_id,
        "url": page_info["url"],
        "title": page_info["title"],
        "screenshot": screenshot,
        "status": "active"
    }


async def close_session(session_id: str) -> bool:
    """
    Close an interactive browser session.

    Args:
        session_id: Session identifier

    Returns:
        True if session was closed, False if not found
    """
    if session_id not in interactive_sessions:
        return False

    browser = interactive_sessions[session_id]
    await browser.stop()
    del interactive_sessions[session_id]

    logger.info(f"Interactive session {session_id} closed")
    return True


async def list_active_sessions() -> list:
    """
    List all active interactive sessions.

    Returns:
        List of session IDs
    """
    return list(interactive_sessions.keys())
