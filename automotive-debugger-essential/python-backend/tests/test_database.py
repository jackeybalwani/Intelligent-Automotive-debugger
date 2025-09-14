"""
Tests for database models and operations
"""

import pytest
import tempfile
import os
from database.models import init_database, get_session, UploadedFile, AnalysisSession, FileStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestDatabaseModels:
    """Test database models and operations"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        # Create a temporary file for the test database
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(temp_fd)

        # Override the database path temporarily
        original_engine = None
        try:
            # Create test database
            engine = create_engine(f'sqlite:///{temp_path}', echo=False)
            Session = sessionmaker(bind=engine)

            # Import and modify the models module temporarily
            from database import models
            original_engine = models.engine
            original_Session = models.Session

            models.engine = engine
            models.Session = Session

            # Create tables
            models.Base.metadata.create_all(engine)

            yield temp_path

        finally:
            # Restore original database configuration
            if original_engine:
                from database import models
                models.engine = original_engine
                models.Session = original_Session

            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    def test_uploaded_file_creation(self, temp_db):
        """Test creating an uploaded file record"""
        session = get_session()

        try:
            # Create a test file record
            test_file = UploadedFile(
                id="test_hash_123",
                filename="test.asc",
                original_path="/tmp/test.asc",
                file_size=1024,
                file_format="CAN ASC",
                status=FileStatus.UPLOADED
            )

            session.add(test_file)
            session.commit()

            # Verify the file was created
            retrieved_file = session.query(UploadedFile).filter_by(id="test_hash_123").first()
            assert retrieved_file is not None
            assert retrieved_file.filename == "test.asc"
            assert retrieved_file.file_format == "CAN ASC"
            assert retrieved_file.status == FileStatus.UPLOADED

        finally:
            session.close()

    def test_analysis_session_creation(self, temp_db):
        """Test creating an analysis session record"""
        session = get_session()

        try:
            # Create a test analysis session
            test_session = AnalysisSession(
                id="analysis_123",
                file_id="test_hash_123",
                status=FileStatus.ANALYZING,
                total_messages=1000,
                unique_ids=50,
                error_count=5
            )

            session.add(test_session)
            session.commit()

            # Verify the session was created
            retrieved_session = session.query(AnalysisSession).filter_by(id="analysis_123").first()
            assert retrieved_session is not None
            assert retrieved_session.file_id == "test_hash_123"
            assert retrieved_session.total_messages == 1000
            assert retrieved_session.unique_ids == 50
            assert retrieved_session.error_count == 5

        finally:
            session.close()

    def test_file_status_enum(self):
        """Test FileStatus enum values"""
        assert FileStatus.UPLOADED.value == "uploaded"
        assert FileStatus.ANALYZING.value == "analyzing"
        assert FileStatus.ANALYZED.value == "analyzed"
        assert FileStatus.ERROR.value == "error"