"""
Database module for SNF Patient Navigator Case Collection App.
Supports SQLite (default) and PostgreSQL via DATABASE_URL environment variable.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Date, ForeignKey, LargeBinary
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
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
    case_id format: {username}_{number} where number is sequential per user (1, 2, 3...)
    """
    __tablename__ = "cases"

    case_id = Column(String(250), primary_key=True)  # Format: username_number (e.g., "john_1")
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    case_start_date = Column(Date, default=FIXED_CASE_START_DATE, nullable=False)
    intake_version = Column(String(50), nullable=False)  # e.g. "abbrev", "full", "follow_on_abbrev"
    
    # User name (who created this case) - case sensitive
    user_name = Column(String(200), nullable=False)
    
    # Demographics (required)
    age_at_snf_stay = Column(Integer, nullable=False)
    gender = Column(Text, nullable=False)
    race = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    snf_name = Column(Text, nullable=True)  # Name of the SNF facility

    # Additional fields
    snf_days = Column(Integer, nullable=True)
    services_discussed = Column(Text, nullable=True)
    services_accepted = Column(Text, nullable=True)
    services_utilized_after_discharge = Column(Text, nullable=True)  # Post-discharge services utilization
    
    # JSON string storing all narrative answers keyed by stable IDs
    answers_json = Column(Text, nullable=False, default="{}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert case to dictionary for display/export."""
        return {
            "case_id": self.case_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "case_start_date": self.case_start_date.isoformat() if self.case_start_date else None,
            "intake_version": self.intake_version,
            "user_name": self.user_name,
            "age_at_snf_stay": self.age_at_snf_stay,
            "gender": self.gender,
            "race": self.race,
            "state": self.state,
            "snf_name": self.snf_name,
            "snf_days": self.snf_days,
            "services_discussed": self.services_discussed,
            "services_accepted": self.services_accepted,
            "services_utilized_after_discharge": self.services_utilized_after_discharge,
            "answers": json.loads(self.answers_json) if self.answers_json else {}
        }


class User(Base):
    """
    SQLAlchemy model for user authentication.
    Users log in with username + 4-digit PIN.
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(200), unique=True, nullable=False)
    pin_hash = Column(String(64), nullable=False)  # SHA-256 hash of PIN
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding pin_hash)."""
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class FollowUpQuestion(Base):
    """
    SQLAlchemy model for AI-generated follow-up questions.
    Each row represents one follow-up question for a case.
    """
    __tablename__ = "follow_up_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(250), ForeignKey("cases.case_id"), nullable=False)
    user_name = Column(String(200), nullable=False)  # User who owns this question
    section = Column(String(1), nullable=False)  # "A", "B", or "C"
    question_number = Column(Integer, nullable=False)  # 1, 2, 3, etc. within section
    question_text = Column(Text, nullable=False)  # The AI-generated question
    answer_text = Column(Text, nullable=True)  # User's answer (nullable if not yet answered)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    answered_at = Column(DateTime, nullable=True)  # When user answered

    def to_dict(self) -> Dict[str, Any]:
        """Convert follow-up question to dictionary."""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "user_name": self.user_name,
            "section": self.section,
            "question_number": self.question_number,
            "question_text": self.question_text,
            "answer_text": self.answer_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "answered_at": self.answered_at.isoformat() if self.answered_at else None,
            "is_answered": self.answer_text is not None
        }


class AudioResponse(Base):
    """
    SQLAlchemy model for audio recordings and transcripts.
    Supports versioning - each edit creates a new row with incremented version_number.
    Can be linked to case questions OR follow-up questions.
    """
    __tablename__ = "audio_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String(250), ForeignKey("cases.case_id"), nullable=False)
    question_id = Column(String(20), nullable=True)  # e.g., "aq1", "q6" - for case questions
    follow_up_question_id = Column(String(36), ForeignKey("follow_up_questions.id"), nullable=True)  # For follow-up questions
    audio_path = Column(Text, nullable=True)  # Path in Supabase Storage
    audio_data = Column(LargeBinary, nullable=True)  # Store audio bytes directly (fallback)
    auto_transcript = Column(Text, nullable=True)  # Original Whisper transcription
    edited_transcript = Column(Text, nullable=True)  # User-edited version
    version_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert audio response to dictionary."""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "question_id": self.question_id,
            "follow_up_question_id": self.follow_up_question_id,
            "audio_path": self.audio_path,
            "has_audio": self.audio_data is not None or self.audio_path is not None,
            "auto_transcript": self.auto_transcript,
            "edited_transcript": self.edited_transcript,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AppSettings(Base):
    """
    SQLAlchemy model for application-wide settings.
    Stores key-value pairs for configuration.
    """
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert setting to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class DraftCase(Base):
    """
    SQLAlchemy model for draft/incomplete cases.
    Stores work-in-progress cases that haven't been finalized yet.
    One draft per user per intake type (abbrev or full).
    """
    __tablename__ = "draft_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = Column(String(200), nullable=False)
    intake_version = Column(String(50), nullable=False)  # e.g. "abbrev", "full", "follow_on_abbrev"

    # Demographics (nullable for drafts - may not be filled yet)
    age_at_snf_stay = Column(Integer, nullable=True)
    gender = Column(Text, nullable=True)
    race = Column(Text, nullable=True)
    state = Column(Text, nullable=True)
    snf_name = Column(Text, nullable=True)

    # Additional fields
    snf_days = Column(Integer, nullable=True)
    services_discussed = Column(Text, nullable=True)
    services_accepted = Column(Text, nullable=True)
    services_utilized_after_discharge = Column(Text, nullable=True)

    # JSON string storing all narrative answers keyed by stable IDs
    answers_json = Column(Text, nullable=False, default="{}")

    # JSON string storing audio data references (question_id -> has_audio boolean)
    audio_json = Column(Text, nullable=False, default="{}")

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow(), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert draft case to dictionary."""
        return {
            "id": self.id,
            "user_name": self.user_name,
            "intake_version": self.intake_version,
            "age_at_snf_stay": self.age_at_snf_stay,
            "gender": self.gender,
            "race": self.race,
            "state": self.state,
            "snf_days": self.snf_days,
            "services_discussed": self.services_discussed,
            "services_accepted": self.services_accepted,
            "answers": json.loads(self.answers_json) if self.answers_json else {},
            "audio": json.loads(self.audio_json) if self.audio_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============== Authentication Functions ==============

def hash_pin(pin: str) -> str:
    """Hash a 4-digit PIN using SHA-256."""
    return hashlib.sha256(pin.encode()).hexdigest()


def create_user(username: str, pin: str) -> Optional[str]:
    """
    Create a new user with username and 4-digit PIN.

    Args:
        username: User's full name (case insensitive for matching)
        pin: 4-digit PIN

    Returns:
        User ID if created successfully, None if username already exists
    """
    session = get_session()
    try:
        # Check if username already exists (case insensitive)
        from sqlalchemy import func
        existing = session.query(User).filter(func.lower(User.username) == username.lower()).first()
        if existing:
            return None

        user = User(
            username=username,
            pin_hash=hash_pin(pin)
        )
        session.add(user)
        session.commit()
        return user.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def authenticate_user(username: str, pin: str) -> Optional[User]:
    """
    Authenticate a user with username and PIN.

    Args:
        username: User's full name (case insensitive)
        pin: 4-digit PIN

    Returns:
        User object if authentication successful, None otherwise
    """
    session = get_session()
    try:
        from sqlalchemy import func
        user = session.query(User).filter(
            func.lower(User.username) == username.lower(),
            User.pin_hash == hash_pin(pin)
        ).first()
        if user:
            session.expunge(user)
        return user
    finally:
        session.close()


def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username (case insensitive)."""
    session = get_session()
    try:
        from sqlalchemy import func
        user = session.query(User).filter(func.lower(User.username) == username.lower()).first()
        if user:
            session.expunge(user)
        return user
    finally:
        session.close()


def get_all_users() -> List[User]:
    """Get all registered users."""
    session = get_session()
    try:
        users = session.query(User).order_by(User.username.asc()).all()
        for user in users:
            session.expunge(user)
        return users
    finally:
        session.close()


# ============== Audio Response Functions ==============

def save_audio_response(
    case_id: str,
    question_id: str,
    audio_data: Optional[bytes] = None,
    audio_path: Optional[str] = None,
    auto_transcript: Optional[str] = None,
    edited_transcript: Optional[str] = None
) -> str:
    """
    Save an audio response with transcription. Creates version 1.

    Args:
        case_id: The case this response belongs to
        question_id: The question ID (e.g., "aq1", "q6")
        audio_data: Raw audio bytes (optional)
        audio_path: Path to audio in Supabase Storage (optional)
        auto_transcript: Original Whisper transcription
        edited_transcript: User-edited transcript (optional)

    Returns:
        The audio response ID
    """
    session = get_session()
    try:
        response = AudioResponse(
            case_id=case_id,
            question_id=question_id,
            audio_data=audio_data,
            audio_path=audio_path,
            auto_transcript=auto_transcript,
            edited_transcript=edited_transcript,
            version_number=1
        )
        session.add(response)
        session.commit()
        return response.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_transcript_version(
    case_id: str,
    question_id: str,
    edited_transcript: str,
    auto_transcript: Optional[str] = None,
    audio_data: Optional[bytes] = None,
    audio_path: Optional[str] = None
) -> str:
    """
    Save a new version of a transcript. Increments version number automatically.

    Args:
        case_id: The case this response belongs to
        question_id: The question ID
        edited_transcript: The new edited transcript
        auto_transcript: Original transcript (copied from previous if not provided)
        audio_data: Audio bytes (copied from previous if not provided)
        audio_path: Audio path (copied from previous if not provided)

    Returns:
        The new audio response ID
    """
    session = get_session()
    try:
        # Get the latest version for this case/question
        latest = session.query(AudioResponse).filter(
            AudioResponse.case_id == case_id,
            AudioResponse.question_id == question_id
        ).order_by(AudioResponse.version_number.desc()).first()

        new_version = 1
        if latest:
            new_version = latest.version_number + 1
            # Copy audio data from previous version if not provided
            if audio_data is None and latest.audio_data:
                audio_data = latest.audio_data
            if audio_path is None and latest.audio_path:
                audio_path = latest.audio_path
            if auto_transcript is None and latest.auto_transcript:
                auto_transcript = latest.auto_transcript

        response = AudioResponse(
            case_id=case_id,
            question_id=question_id,
            audio_data=audio_data,
            audio_path=audio_path,
            auto_transcript=auto_transcript,
            edited_transcript=edited_transcript,
            version_number=new_version
        )
        session.add(response)
        session.commit()
        return response.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_audio_responses_for_case(case_id: str) -> List[AudioResponse]:
    """
    Get all audio responses for a case (all questions, all versions).

    Args:
        case_id: The case ID

    Returns:
        List of AudioResponse objects ordered by question_id, version_number
    """
    session = get_session()
    try:
        responses = session.query(AudioResponse).filter(
            AudioResponse.case_id == case_id
        ).order_by(
            AudioResponse.question_id.asc(),
            AudioResponse.version_number.asc()
        ).all()
        for r in responses:
            session.expunge(r)
        return responses
    finally:
        session.close()


def get_audio_response_versions(case_id: str, question_id: str) -> List[AudioResponse]:
    """
    Get all versions of an audio response for a specific question.

    Args:
        case_id: The case ID
        question_id: The question ID

    Returns:
        List of AudioResponse objects ordered by version_number ascending
    """
    session = get_session()
    try:
        responses = session.query(AudioResponse).filter(
            AudioResponse.case_id == case_id,
            AudioResponse.question_id == question_id
        ).order_by(AudioResponse.version_number.asc()).all()
        for r in responses:
            session.expunge(r)
        return responses
    finally:
        session.close()


def get_latest_audio_response(case_id: str, question_id: str) -> Optional[AudioResponse]:
    """
    Get the latest version of an audio response for a specific question.

    Args:
        case_id: The case ID
        question_id: The question ID

    Returns:
        The latest AudioResponse or None
    """
    session = get_session()
    try:
        response = session.query(AudioResponse).filter(
            AudioResponse.case_id == case_id,
            AudioResponse.question_id == question_id
        ).order_by(AudioResponse.version_number.desc()).first()
        if response:
            session.expunge(response)
        return response
    finally:
        session.close()


# ============== App Settings Functions ==============

# Default settings for Whisper transcription
DEFAULT_SETTINGS = {
    "whisper_model_size": "base",  # tiny, base, small, medium, large
    "whisper_model_version": "openai-whisper",  # openai-whisper, or future: granite-3.3
}


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an application setting by key.

    Args:
        key: The setting key
        default: Default value if setting doesn't exist

    Returns:
        The setting value or default
    """
    session = get_session()
    try:
        setting = session.query(AppSettings).filter(AppSettings.key == key).first()
        if setting:
            return setting.value
        return default if default is not None else DEFAULT_SETTINGS.get(key)
    finally:
        session.close()


def set_setting(key: str, value: str) -> None:
    """
    Set an application setting.

    Args:
        key: The setting key
        value: The setting value
    """
    session = get_session()
    try:
        setting = session.query(AppSettings).filter(AppSettings.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = AppSettings(key=key, value=value)
            session.add(setting)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_all_settings() -> Dict[str, str]:
    """
    Get all application settings.

    Returns:
        Dictionary of all settings with defaults filled in
    """
    session = get_session()
    try:
        settings = session.query(AppSettings).all()
        result = DEFAULT_SETTINGS.copy()
        for s in settings:
            result[s.key] = s.value
        return result
    finally:
        session.close()


def get_whisper_settings() -> Dict[str, str]:
    """
    Get Whisper-specific settings.

    Returns:
        Dictionary with whisper_model_size and whisper_model_version
    """
    return {
        "model_size": get_setting("whisper_model_size", "base"),
        "model_version": get_setting("whisper_model_version", "openai-whisper")
    }


def _run_migrations():
    """
    Run database migrations to add new columns if they don't exist.
    This ensures backward compatibility when new fields are added to models.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)

    # Define migrations: (table_name, column_name, column_type)
    migrations = [
        # Cases table migrations
        ("cases", "snf_name", "TEXT"),
        ("cases", "services_utilized_after_discharge", "TEXT"),
        # Draft cases table migrations
        ("draft_cases", "snf_name", "TEXT"),
        ("draft_cases", "services_utilized_after_discharge", "TEXT"),
    ]

    with engine.connect() as conn:
        for table_name, column_name, column_type in migrations:
            # Check if table exists
            if table_name not in inspector.get_table_names():
                continue

            # Get existing columns
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]

            # Add column if it doesn't exist
            if column_name not in existing_columns:
                try:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))
                    conn.commit()
                except Exception as e:
                    # Column might already exist or other error - log and continue
                    print(f"Migration note: Could not add {column_name} to {table_name}: {e}")

        # Widen intake_version column for follow-on draft support (VARCHAR(10) -> VARCHAR(50))
        for table_name in ("cases", "draft_cases"):
            if table_name not in inspector.get_table_names():
                continue
            try:
                # PostgreSQL: alter column type
                conn.execute(text(
                    f"ALTER TABLE {table_name} ALTER COLUMN intake_version TYPE VARCHAR(50)"
                ))
                conn.commit()
            except Exception:
                # SQLite doesn't enforce VARCHAR length, so this is a no-op there
                pass


def init_db():
    """Initialize database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

    # Run migrations to add new columns if they don't exist
    _run_migrations()


def get_session():
    """Get a new database session."""
    return SessionLocal()


def get_next_case_number(user_name: str) -> int:
    """
    Get the next case number for a user.

    Args:
        user_name: The user's name (case insensitive)

    Returns:
        The next case number (1 if first case, otherwise max + 1)
    """
    session = get_session()
    try:
        from sqlalchemy import func
        # Get all cases for this user and count them
        count = session.query(Case).filter(
            func.lower(Case.user_name) == user_name.lower()
        ).count()
        return count + 1
    finally:
        session.close()


def generate_case_id(user_name: str, case_number: int) -> str:
    """
    Generate a case ID in the format: username_number

    Args:
        user_name: The user's name
        case_number: The sequential case number for this user

    Returns:
        Case ID string (e.g., "john_doe_1")
    """
    # Normalize username: lowercase, replace spaces with underscores
    normalized_name = user_name.lower().replace(" ", "_")
    return f"{normalized_name}_{case_number}"


def create_case(
    intake_version: str,
    user_name: str,
    age_at_snf_stay: int,
    gender: str,
    race: str,
    state: str,
    snf_name: Optional[str],
    snf_days: Optional[int],
    services_discussed: Optional[str],
    services_accepted: Optional[str],
    services_utilized_after_discharge: Optional[str],
    answers: Dict[str, str]
) -> str:
    """
    Create a new case record in the database.

    Args:
        intake_version: "abbrev" or "full"
        user_name: Full name of the user creating this case (case sensitive)
        age_at_snf_stay: Patient's age during SNF stay
        gender: Patient's gender
        race: Patient's race
        state: State where SNF is located
        snf_name: Name of the SNF facility (nullable)
        snf_days: Number of days in SNF (nullable)
        services_discussed: Free text of services discussed
        services_accepted: Free text of services accepted
        services_utilized_after_discharge: Whether patient used services after discharge (nullable)
        answers: Dictionary of narrative answers keyed by question ID

    Returns:
        The generated case_id (format: username_number, e.g., "john_doe_1")
    """
    session = get_session()
    try:
        # Generate sequential case_id for this user
        case_number = get_next_case_number(user_name)
        case_id = generate_case_id(user_name, case_number)

        case = Case(
            case_id=case_id,
            intake_version=intake_version,
            user_name=user_name,
            age_at_snf_stay=age_at_snf_stay,
            gender=gender,
            race=race,
            state=state,
            snf_name=snf_name,
            snf_days=snf_days,
            services_discussed=services_discussed,
            services_accepted=services_accepted,
            services_utilized_after_discharge=services_utilized_after_discharge,
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


def get_cases_by_user_name(user_name: str) -> List[Case]:
    """
    Retrieve all cases created by a specific user.

    Args:
        user_name: The user's full name (case insensitive)

    Returns:
        List of Case objects ordered by created_at ascending (oldest first for numbering)
    """
    session = get_session()
    try:
        from sqlalchemy import func
        cases = session.query(Case).filter(func.lower(Case.user_name) == user_name.lower()).order_by(Case.created_at.asc()).all()
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


def get_all_user_names() -> List[str]:
    """
    Get all unique user names for admin dropdown.

    Returns:
        List of unique user_name strings sorted alphabetically
    """
    session = get_session()
    try:
        result = session.query(Case.user_name).distinct().order_by(Case.user_name.asc()).all()
        return [r[0] for r in result]
    finally:
        session.close()


# ============== Follow-Up Question Functions ==============

def create_follow_up_questions(case_id: str, questions: List[Dict[str, Any]], user_name: str) -> List[str]:
    """
    Create multiple follow-up questions for a case.

    Args:
        case_id: The case ID these questions belong to
        questions: List of dicts with keys: section, question_number, question_text
        user_name: The user who owns these questions

    Returns:
        List of created question IDs
    """
    session = get_session()
    try:
        question_ids = []
        for q in questions:
            follow_up = FollowUpQuestion(
                case_id=case_id,
                user_name=user_name,
                section=q["section"],
                question_number=q["question_number"],
                question_text=q["question_text"]
            )
            session.add(follow_up)
            session.flush()  # Get the ID
            question_ids.append(follow_up.id)
        session.commit()
        return question_ids
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_follow_up_questions_for_case(case_id: str) -> List[FollowUpQuestion]:
    """
    Get all follow-up questions for a case, ordered by section and question number.

    Args:
        case_id: The case ID

    Returns:
        List of FollowUpQuestion objects
    """
    session = get_session()
    try:
        questions = session.query(FollowUpQuestion).filter(
            FollowUpQuestion.case_id == case_id
        ).order_by(
            FollowUpQuestion.section.asc(),
            FollowUpQuestion.question_number.asc()
        ).all()
        for q in questions:
            session.expunge(q)
        return questions
    finally:
        session.close()


def get_unanswered_follow_up_questions(case_id: str) -> List[FollowUpQuestion]:
    """
    Get unanswered follow-up questions for a case.

    Args:
        case_id: The case ID

    Returns:
        List of unanswered FollowUpQuestion objects
    """
    session = get_session()
    try:
        questions = session.query(FollowUpQuestion).filter(
            FollowUpQuestion.case_id == case_id,
            FollowUpQuestion.answer_text.is_(None)
        ).order_by(
            FollowUpQuestion.section.asc(),
            FollowUpQuestion.question_number.asc()
        ).all()
        for q in questions:
            session.expunge(q)
        return questions
    finally:
        session.close()


def update_follow_up_answer(question_id: str, answer_text: str) -> bool:
    """
    Update the answer for a follow-up question.

    Args:
        question_id: The follow-up question ID
        answer_text: The user's answer

    Returns:
        True if updated successfully, False if question not found
    """
    session = get_session()
    try:
        question = session.query(FollowUpQuestion).filter(
            FollowUpQuestion.id == question_id
        ).first()
        if question:
            question.answer_text = answer_text
            question.answered_at = datetime.utcnow()
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_cases_with_pending_follow_ups(user_name: str) -> List[Dict[str, Any]]:
    """
    Get cases that have unanswered follow-up questions for a user.

    Args:
        user_name: The user's name (case insensitive)

    Returns:
        List of dicts with case info and pending question count
    """
    session = get_session()
    try:
        from sqlalchemy import func

        # Get all cases for the user that have follow-up questions
        cases = session.query(Case).filter(
            func.lower(Case.user_name) == user_name.lower()
        ).order_by(Case.created_at.desc()).all()

        result = []
        for case in cases:
            # Count total and unanswered questions
            total_questions = session.query(FollowUpQuestion).filter(
                FollowUpQuestion.case_id == case.case_id
            ).count()

            if total_questions > 0:
                unanswered = session.query(FollowUpQuestion).filter(
                    FollowUpQuestion.case_id == case.case_id,
                    FollowUpQuestion.answer_text.is_(None)
                ).count()

                result.append({
                    "case_id": case.case_id,
                    "intake_version": case.intake_version,
                    "created_at": case.created_at,
                    "age_at_snf_stay": case.age_at_snf_stay,
                    "race": case.race,
                    "state": case.state,
                    "total_questions": total_questions,
                    "answered_questions": total_questions - unanswered,
                    "unanswered_questions": unanswered,
                    "is_complete": unanswered == 0
                })

        return result
    finally:
        session.close()


def get_follow_up_question_by_id(question_id: str) -> Optional[FollowUpQuestion]:
    """
    Get a single follow-up question by ID.

    Args:
        question_id: The follow-up question ID

    Returns:
        FollowUpQuestion object or None
    """
    session = get_session()
    try:
        question = session.query(FollowUpQuestion).filter(
            FollowUpQuestion.id == question_id
        ).first()
        if question:
            session.expunge(question)
        return question
    finally:
        session.close()


def case_has_follow_up_questions(case_id: str) -> bool:
    """
    Check if a case has any follow-up questions generated.

    Args:
        case_id: The case ID

    Returns:
        True if case has follow-up questions, False otherwise
    """
    session = get_session()
    try:
        count = session.query(FollowUpQuestion).filter(
            FollowUpQuestion.case_id == case_id
        ).count()
        return count > 0
    finally:
        session.close()


# ============== Follow-Up Audio Functions ==============

def save_follow_up_audio_response(
    case_id: str,
    follow_up_question_id: str,
    audio_data: Optional[bytes] = None,
    audio_path: Optional[str] = None,
    auto_transcript: Optional[str] = None,
    edited_transcript: Optional[str] = None
) -> str:
    """
    Save an audio response for a follow-up question. Creates version 1.

    Args:
        case_id: The case this response belongs to
        follow_up_question_id: The follow-up question ID
        audio_data: Raw audio bytes (optional)
        audio_path: Path to audio in storage (optional)
        auto_transcript: Original Whisper transcription
        edited_transcript: User-edited transcript (optional)

    Returns:
        The audio response ID
    """
    session = get_session()
    try:
        # Use a question_id that identifies this as a follow-up question audio
        # Format: "fu_<first 12 chars of follow_up_question_id>" to fit in 20 char limit
        question_id = f"fu_{follow_up_question_id[:12]}"

        response = AudioResponse(
            case_id=case_id,
            question_id=question_id,
            follow_up_question_id=follow_up_question_id,
            audio_data=audio_data,
            audio_path=audio_path,
            auto_transcript=auto_transcript,
            edited_transcript=edited_transcript,
            version_number=1
        )
        session.add(response)
        session.commit()
        return response.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_latest_follow_up_audio(case_id: str, follow_up_question_id: str) -> Optional[AudioResponse]:
    """
    Get the latest audio response for a follow-up question.

    Args:
        case_id: The case ID
        follow_up_question_id: The follow-up question ID

    Returns:
        The latest AudioResponse or None
    """
    session = get_session()
    try:
        response = session.query(AudioResponse).filter(
            AudioResponse.case_id == case_id,
            AudioResponse.follow_up_question_id == follow_up_question_id
        ).order_by(AudioResponse.version_number.desc()).first()
        if response:
            session.expunge(response)
        return response
    finally:
        session.close()


# ============== Draft Case Functions ==============

def save_draft_case(
    user_name: str,
    intake_version: str,
    age_at_snf_stay: Optional[int] = None,
    gender: Optional[str] = None,
    race: Optional[str] = None,
    state: Optional[str] = None,
    snf_name: Optional[str] = None,
    snf_days: Optional[int] = None,
    services_discussed: Optional[str] = None,
    services_accepted: Optional[str] = None,
    services_utilized_after_discharge: Optional[str] = None,
    answers: Optional[Dict[str, str]] = None,
    audio_flags: Optional[Dict[str, bool]] = None
) -> str:
    """
    Save or update a draft case. Only one draft per user per intake type.

    Args:
        user_name: The user's name
        intake_version: "abbrev" or "full"
        age_at_snf_stay: Patient's age (nullable)
        gender: Patient's gender (nullable)
        race: Patient's race (nullable)
        state: SNF state (nullable)
        snf_name: Name of the SNF facility (nullable)
        snf_days: Number of days in SNF (nullable)
        services_discussed: Services discussed text (nullable)
        services_accepted: Services accepted text (nullable)
        services_utilized_after_discharge: Whether patient used services after discharge (nullable)
        answers: Dictionary of narrative answers
        audio_flags: Dictionary of question_id -> bool indicating if audio exists

    Returns:
        The draft case ID
    """
    session = get_session()
    try:
        from sqlalchemy import func

        # Check if draft already exists for this user and intake type
        existing = session.query(DraftCase).filter(
            func.lower(DraftCase.user_name) == user_name.lower(),
            DraftCase.intake_version == intake_version
        ).first()

        if existing:
            # Update existing draft
            existing.age_at_snf_stay = age_at_snf_stay
            existing.gender = gender
            existing.race = race
            existing.state = state
            existing.snf_name = snf_name
            existing.snf_days = snf_days
            existing.services_discussed = services_discussed
            existing.services_accepted = services_accepted
            existing.services_utilized_after_discharge = services_utilized_after_discharge
            existing.answers_json = json.dumps(answers or {})
            existing.audio_json = json.dumps(audio_flags or {})
            existing.updated_at = datetime.utcnow()
            session.commit()
            return existing.id
        else:
            # Create new draft
            draft = DraftCase(
                user_name=user_name,
                intake_version=intake_version,
                age_at_snf_stay=age_at_snf_stay,
                gender=gender,
                race=race,
                state=state,
                snf_name=snf_name,
                snf_days=snf_days,
                services_discussed=services_discussed,
                services_accepted=services_accepted,
                services_utilized_after_discharge=services_utilized_after_discharge,
                answers_json=json.dumps(answers or {}),
                audio_json=json.dumps(audio_flags or {})
            )
            session.add(draft)
            session.commit()
            return draft.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_draft_case(user_name: str, intake_version: str) -> Optional[DraftCase]:
    """
    Get a user's draft case for a specific intake type.

    Args:
        user_name: The user's name (case insensitive)
        intake_version: "abbrev" or "full"

    Returns:
        DraftCase object if found, None otherwise
    """
    session = get_session()
    try:
        from sqlalchemy import func
        draft = session.query(DraftCase).filter(
            func.lower(DraftCase.user_name) == user_name.lower(),
            DraftCase.intake_version == intake_version
        ).first()
        if draft:
            session.expunge(draft)
        return draft
    finally:
        session.close()


def has_draft_case(user_name: str, intake_version: str) -> bool:
    """
    Check if a user has a draft case for a specific intake type.

    Args:
        user_name: The user's name (case insensitive)
        intake_version: "abbrev" or "full"

    Returns:
        True if draft exists, False otherwise
    """
    session = get_session()
    try:
        from sqlalchemy import func
        count = session.query(DraftCase).filter(
            func.lower(DraftCase.user_name) == user_name.lower(),
            DraftCase.intake_version == intake_version
        ).count()
        return count > 0
    finally:
        session.close()


def delete_draft_case(user_name: str, intake_version: str) -> bool:
    """
    Delete a user's draft case for a specific intake type.

    Args:
        user_name: The user's name (case insensitive)
        intake_version: "abbrev" or "full"

    Returns:
        True if deleted, False if not found
    """
    session = get_session()
    try:
        from sqlalchemy import func
        draft = session.query(DraftCase).filter(
            func.lower(DraftCase.user_name) == user_name.lower(),
            DraftCase.intake_version == intake_version
        ).first()
        if draft:
            session.delete(draft)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_all_user_drafts(user_name: str) -> List[DraftCase]:
    """
    Get all draft cases for a user.

    Args:
        user_name: The user's name (case insensitive)

    Returns:
        List of DraftCase objects
    """
    session = get_session()
    try:
        from sqlalchemy import func
        drafts = session.query(DraftCase).filter(
            func.lower(DraftCase.user_name) == user_name.lower()
        ).order_by(DraftCase.updated_at.desc()).all()
        for draft in drafts:
            session.expunge(draft)
        return drafts
    finally:
        session.close()


# Initialize database on module import
init_db()

