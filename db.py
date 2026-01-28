"""
Database module for SNF Patient Navigator Case Collection App.
Supports SQLite (default) and PostgreSQL via DATABASE_URL environment variable.
"""

import os
import json
import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Date
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# Default to SQLite for development
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///snf_cases.db")

# Handle postgres:// vs postgresql:// (Heroku uses postgres://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
else:
    engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Fixed case start date as specified
FIXED_CASE_START_DATE = date(2025, 1, 1)


class Case(Base):
    """
    SQLAlchemy model for SNF patient navigator cases.
    Stores one row per case with demographics and narrative answers as JSON.
    """
    __tablename__ = "cases"

    case_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    case_start_date = Column(Date, default=FIXED_CASE_START_DATE, nullable=False)
    intake_version = Column(String(10), nullable=False)  # "abbrev" or "full"
    
    # User ID (who created this case)
    user_id = Column(String(100), nullable=False)
    
    # Demographics (required)
    age_at_snf_stay = Column(Integer, nullable=False)
    gender = Column(Text, nullable=False)
    race = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    
    # Additional fields
    snf_days = Column(Integer, nullable=True)
    services_discussed = Column(Text, nullable=True)
    services_accepted = Column(Text, nullable=True)
    
    # JSON string storing all narrative answers keyed by stable IDs
    answers_json = Column(Text, nullable=False, default="{}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert case to dictionary for display/export."""
        return {
            "case_id": self.case_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "case_start_date": self.case_start_date.isoformat() if self.case_start_date else None,
            "intake_version": self.intake_version,
            "user_id": self.user_id,
            "age_at_snf_stay": self.age_at_snf_stay,
            "gender": self.gender,
            "race": self.race,
            "state": self.state,
            "snf_days": self.snf_days,
            "services_discussed": self.services_discussed,
            "services_accepted": self.services_accepted,
            "answers": json.loads(self.answers_json) if self.answers_json else {}
        }


def init_db():
    """Initialize database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a new database session."""
    return SessionLocal()


def create_case(
    intake_version: str,
    user_id: str,
    age_at_snf_stay: int,
    gender: str,
    race: str,
    state: str,
    snf_days: Optional[int],
    services_discussed: Optional[str],
    services_accepted: Optional[str],
    answers: Dict[str, str]
) -> str:
    """
    Create a new case record in the database.
    
    Args:
        intake_version: "abbrev" or "full"
        user_id: ID of the user creating this case
        age_at_snf_stay: Patient's age during SNF stay
        gender: Patient's gender
        race: Patient's race
        state: State where SNF is located
        snf_days: Number of days in SNF (nullable)
        services_discussed: Free text of services discussed
        services_accepted: Free text of services accepted
        answers: Dictionary of narrative answers keyed by question ID
    
    Returns:
        The generated case_id (UUID string)
    """
    session = get_session()
    try:
        case = Case(
            intake_version=intake_version,
            user_id=user_id,
            age_at_snf_stay=age_at_snf_stay,
            gender=gender,
            race=race,
            state=state,
            snf_days=snf_days,
            services_discussed=services_discussed,
            services_accepted=services_accepted,
            answers_json=json.dumps(answers)
        )
        session.add(case)
        session.commit()
        return case.case_id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_case_by_id(case_id: str) -> Optional[Case]:
    """
    Retrieve a case by its ID.
    
    Args:
        case_id: UUID string of the case
    
    Returns:
        Case object if found, None otherwise
    """
    session = get_session()
    try:
        case = session.query(Case).filter(Case.case_id == case_id).first()
        if case:
            # Detach from session for safe use
            session.expunge(case)
        return case
    finally:
        session.close()


def get_cases_by_user_id(user_id: str) -> List[Case]:
    """
    Retrieve all cases created by a specific user.
    
    Args:
        user_id: The user's ID
    
    Returns:
        List of Case objects ordered by created_at descending
    """
    session = get_session()
    try:
        cases = session.query(Case).filter(Case.user_id == user_id).order_by(Case.created_at.desc()).all()
        # Detach from session
        for case in cases:
            session.expunge(case)
        return cases
    finally:
        session.close()


def get_recent_cases(limit: int = 20) -> List[Case]:
    """
    Get the most recent cases.
    
    Args:
        limit: Maximum number of cases to return
    
    Returns:
        List of Case objects ordered by created_at descending
    """
    session = get_session()
    try:
        cases = session.query(Case).order_by(Case.created_at.desc()).limit(limit).all()
        # Detach from session
        for case in cases:
            session.expunge(case)
        return cases
    finally:
        session.close()


def get_all_case_ids() -> List[str]:
    """
    Get all case IDs for search/autocomplete.
    
    Returns:
        List of case_id strings
    """
    session = get_session()
    try:
        result = session.query(Case.case_id).order_by(Case.created_at.desc()).all()
        return [r[0] for r in result]
    finally:
        session.close()


# Initialize database on module import
init_db()

