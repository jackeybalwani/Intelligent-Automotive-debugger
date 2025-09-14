"""
Database Models
SQLAlchemy models for the application
"""

import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

logger = logging.getLogger(__name__)

Base = declarative_base()
class FileStatus(enum.Enum):

    UPLOADED = "uploaded"

    ANALYZING = "analyzing" 

    ANALYZED = "analyzed"

    ERROR = "error"



class UploadedFile(Base):

    """Track uploaded files with status"""

    __tablename__ = 'uploaded_files'

    

    id = Column(String(64), primary_key=True)  # file hash

    filename = Column(String(255), nullable=False)

    original_path = Column(String(500))

    file_size = Column(Integer)

    file_format = Column(String(50))  # CAN ASC, CAN BLF, etc.

    status = Column(Enum(FileStatus), default=FileStatus.UPLOADED)

    upload_timestamp = Column(DateTime, default=datetime.utcnow)

    analysis_timestamp = Column(DateTime)

    

    # New fields for UI

    format_confidence = Column(Float, default=0.0)

    error_message = Column(Text)

    processing_progress = Column(Integer, default=0)  # 0-100



class AnalysisSession(Base):

    """Track analysis sessions (one file at a time now)"""

    __tablename__ = 'analysis_sessions'

    

    id = Column(String(64), primary_key=True)

    file_id = Column(String(64), nullable=False)  # Single file now

    created_at = Column(DateTime, default=datetime.utcnow)

    completed_at = Column(DateTime)

    status = Column(Enum(FileStatus), default=FileStatus.ANALYZING)

    

    # Analysis results - structured for new UI

    total_messages = Column(Integer, default=0)

    unique_ids = Column(Integer, default=0)

    time_range_start = Column(Float, default=0.0)

    time_range_end = Column(Float, default=0.0)

    error_count = Column(Integer, default=0)

    

    # JSON fields for detailed results

    errors = Column(JSON)  # List of errors with severity, timestamps

    patterns = Column(JSON)  # Bus load, dominant IDs, etc.

    timeline_data = Column(JSON)  # Timeline visualization data

    statistics = Column(JSON)  # Additional file-specific stats

class AnalysisHistory(Base):
    """Analysis history table"""
    __tablename__ = 'analysis_history'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), unique=True)
    analysis_result = Column(JSON)
    ai_insights = Column(JSON)
    user_notes = Column(Text)

class PatternLibrary(Base):
    """Pattern library table"""
    __tablename__ = 'pattern_library'
    
    id = Column(Integer, primary_key=True)
    pattern_hash = Column(String(64), unique=True)
    pattern_type = Column(String(100))
    description = Column(Text)
    occurrence_count = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    solution = Column(JSON)
    confidence_score = Column(Float)

class ToolConfigs(Base):
    """Tool configurations table"""
    __tablename__ = 'tool_configs'
    
    tool_name = Column(String(100), primary_key=True)
    version = Column(String(50))
    install_path = Column(String(500))
    import_settings = Column(JSON)
    last_used = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = None
Session = None

def init_database():
    """Initialize database connection"""
    global engine, Session
    
    try:
        # Create SQLite database
        engine = create_engine('sqlite:///database/app.db', echo=False)
        Session = sessionmaker(bind=engine)
        
        # Create tables
        Base.metadata.create_all(engine)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def get_session():
    """Get database session"""
    if Session is None:
        init_database()
    return Session()
