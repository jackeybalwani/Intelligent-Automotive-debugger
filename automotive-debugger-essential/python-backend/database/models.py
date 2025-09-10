"""
Database Models
SQLAlchemy models for the application
"""

import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

logger = logging.getLogger(__name__)

Base = declarative_base()

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
