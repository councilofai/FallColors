"""Database models and session management."""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

from app.core.config import get_settings

settings = get_settings()

# Create database engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TestSession(Base):
    """Model for chatbot test sessions."""

    __tablename__ = "test_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    max_rounds = Column(Integer, nullable=False)
    adversarial_intensity = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Selectors for chatbot interface
    input_selector = Column(String, nullable=True)
    submit_selector = Column(String, nullable=True)
    headless = Column(Boolean, default=False)  # Whether to run browser in headless mode

    # Results
    conversation = Column(JSON, default=list)  # List of message exchanges
    safety_scores = Column(JSON, default=list)  # Safety scores per round
    overall_safety_score = Column(Float, nullable=True)
    vulnerabilities_found = Column(JSON, default=list)  # List of identified issues
    recommendations = Column(JSON, default=list)  # Recommendations for improvement

    # Metadata
    error_message = Column(Text, nullable=True)
    screenshots = Column(JSON, default=list)  # List of screenshot paths/URLs


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
