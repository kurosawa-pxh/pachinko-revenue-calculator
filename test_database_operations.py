#!/usr/bin/env python3
"""
Comprehensive test suite for DatabaseManager CRUD operations and data integrity.
Tests database operations, transaction management, and data consistency.
"""

from src.database import DatabaseManager
from src.database import DatabaseManager, DatabaseError
from src.models import GameSession, ValidationError
import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


# Define DatabaseError locally to avoid circular import

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


# Import DatabaseManager after defining DatabaseError


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_manager(temp_db):
    """Create a DatabaseManager instance with temporary database."""
    return DatabaseManager(temp_db)


@pytest.fixture
def sample_session():
    """Create a sample GameSession for testing."""
    return GameSession(
        user_id="test_user_123",
        date=datetime(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 10, 0),
        store_name="テストホール太郎",
        machine_name="CR花の慶次",
        initial_investment=10000
    )


@pytest.fixture
def completed_session():
    """Create a completed GameSession for testing."""
    session = GameSession(
        user_id="test_user_123",
        date=datetime(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 10, 0),
        store_name="テストホール太郎",
        machine_name="CR花の慶次",
        initial_investment=10000
    )
    session.complete_session(
        end_time=datetime(2024, 1, 15, 12, 0),
        final_investment=15000,
        return_amount=20000
    )
    return session


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""

    def test_database_initialization(self, temp_db):
        """Test successful database initialization."""
        db_manager = DatabaseManager(temp_db)

        # Check that database file was created
        assert os.path.exists(temp_db)

        # Check that tables were created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='game_sessions'
            """)
            assert cursor.fetchone() is not None

    def test_schema_version_tracking(self, temp_db):
        """Test schema version tracking functionality."""
        db_manager = DatabaseManager(temp_db)

        # Check schema version table exists
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            assert cursor.fetchone() is not None

            # Check current version
            cursor = conn.execute("SELECT MAX(version) FROM schema_version")
            version = cursor.fetchone()[0]
            assert version == DatabaseManager.CURRENT_SCHEMA_VERSION

    def test_indexes_creation(self, temp_db):
        """Test that performance indexes are created."""
        db_manager = DatabaseManager(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            # Check required indexes exist
            required_indexes = [
                'idx_user_date',
                'idx_user_month',
                'idx_user_completed',
                'idx_date_desc',
                'idx_user_machine',
                'idx_user_store',
                'idx_created_at'
            ]

            for required_index in required_indexes:
                assert required_index in indexes

    def test_database_constraints(self, temp_db):
        """Test that database constraints are properly enforced."""
        db_manager = DatabaseManager(temp_db)

        # Test constraint enforcement by trying to insert invalid data directly
        with sqlite3.connect(temp_db) as conn:
            # Test negative initial_investment constraint
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute("""
                    INSERT INTO game_sessions 
                    (user_id, date, start_time, store_name, machine_name, initial_investment)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, ("test", "2024-01-15", "2024-01-15 10:00:00", "store", "machine", -1000))


class TestCRUDOperations:
    """Test Create, Read, Update, Delete operations."""

    def test_create_session_success(self, db_manager, sample_session):
        """Test successful session creation."""
        session_id = db_manager.create_session(sample_session)

        assert session_id is not None
        assert isinstance(session_id, int)
        assert session_id > 0
        assert sample_session.id == session_id

    def test_create_session_validation_error(self, db_manager):
        """Test session creation with validation errors."""
        # Test with invalid session data
        with pytest.raises(ValidationError):
            invalid_session = GameSession(
                user_id="",  # Empty user_id should fail
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            db_manager.create_session(invalid_session)

    def test_get_session_success(self, db_manager, sample_session):
        """Test successful session retrieval."""
        # Create session first
        session_id = db_manager.create_session(sample_session)

        # Retrieve session
        retrieved_session = db_manager.get_session(session_id)

        assert retrieved_session is not None
        assert retrieved_session.id == session_id
        assert retrieved_session.user_id == sample_session.user_id
        assert retrieved_session.store_name == sample_session.store_name
        assert retrieved_session.machine_name == sample_session.machine_name
        assert retrieved_session.initial_investment == sample_session.initial_investment

    def test_get_session_not_found(self, db_manager):
        """Test retrieving non-existent session."""
        retrieved_session = db_manager.get_session(99999)
        assert retrieved_session is None

    def test_update_session_success(self, db_manager, sample_session):
        """Test successful session update."""
        # Create session first
        session_id = db_manager.create_session(sample_session)

        # Complete the session
        sample_session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )

        # Update session
        result = db_manager.update_session(session_id, sample_session)
        assert result is True

        # Verify update
        updated_session = db_manager.get_session(session_id)
        assert updated_session.is_completed is True
        assert updated_session.final_investment == 15000
        assert updated_session.return_amount == 20000
        assert updated_session.profit == 5000

    def test_update_session_not_found(self, db_manager, sample_session):
        """Test updating non-existent session."""
        with pytest.raises(DatabaseError):
            db_manager.update_session(99999, sample_session)

    def test_update_session_validation_error(self, db_manager, sample_session):
        """Test updating session with validation errors."""
        # Create session first
        session_id = db_manager.create_session(sample_session)

        # Try to update with invalid data
        with pytest.raises(ValidationError):
            sample_session.user_id = ""  # Invalid empty user_id
            db_manager.update_session(session_id, sample_session)

    def test_delete_session_success(self, db_manager, sample_session):
        """Test successful session deletion."""
        # Create session first
        session_id = db_manager.create_session(sample_session)

        # Delete session
        result = db_manager.delete_session(session_id)
        assert result is True

        # Verify deletion
        deleted_session = db_manager.get_session(session_id)
        assert deleted_session is None

    def test_delete_session_not_found(self, db_manager):
        """Test deleting non-existent session."""
        with pytest.raises(DatabaseError):
            db_manager.delete_session(99999)


class TestSessionQueries:
    """Test session query operations."""

    def create_multiple_sessions(self, db_manager, user_id="test_user", count=5):
        """Helper method to create multiple test sessions."""
        sessions = []
        for i in range(count):
            session = GameSession(
                user_id=user_id,
                date=datetime(2024, 1, 15 + i),
                start_time=datetime(2024, 1, 15 + i, 10, 0),
                store_name=f"テストホール{i+1}",
                machine_name=f"CR花の慶次{i+1}",
                initial_investment=10000 + (i * 1000)
            )

            # Complete some sessions
            if i % 2 == 0:
                session.complete_session(
                    end_time=datetime(2024, 1, 15 + i, 12, 0),
                    final_investment=15000 + (i * 1000),
                    return_amount=20000 + (i * 2000)
                )

            session_id = db_manager.create_session(session)
            session.id = session_id
            sessions.append(session)

        return sessions

    def test_get_sessions_all(self, db_manager):
        """Test retrieving all sessions for a user."""
        sessions = self.create_multiple_sessions(db_manager, "test_user", 3)

        retrieved_sessions = db_manager.get_sessions("test_user")

        assert len(retrieved_sessions) == 3
        # Should be ordered by date DESC
        assert retrieved_sessions[0].date >= retrieved_sessions[1].date
        assert retrieved_sessions[1].date >= retrieved_sessions[2].date

    def test_get_sessions_with_date_range(self, db_manager):
        """Test retrieving sessions with date range filtering."""
        sessions = self.create_multiple_sessions(db_manager, "test_user", 5)

        # Get sessions for specific date range
        start_date = datetime(2024, 1, 16)
        end_date = datetime(2024, 1, 18)

        filtered_sessions = db_manager.get_sessions(
            "test_user",
            date_range=(start_date, end_date)
        )

        assert len(filtered_sessions) == 3  # Sessions for 16th, 17th, 18th
        for session in filtered_sessions:
            assert start_date.date() <= session.date.date() <= end_date.date()

    def test_get_sessions_with_pagination(self, db_manager):
        """Test retrieving sessions with pagination."""
        sessions = self.create_multiple_sessions(db_manager, "test_user", 10)

        # Get first page
        page1 = db_manager.get_sessions("test_user", limit=3, offset=0)
        assert len(page1) == 3

        # Get second page
        page2 = db_manager.get_sessions("test_user", limit=3, offset=3)
        assert len(page2) == 3

        # Ensure no overlap
        page1_ids = {s.id for s in page1}
        page2_ids = {s.id for s in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_sessions_as_dict(self, db_manager):
        """Test retrieving sessions as dictionaries."""
        sessions = self.create_multiple_sessions(db_manager, "test_user", 2)

        session_dicts = db_manager.get_sessions_as_dict("test_user")

        assert len(session_dicts) == 2
        assert all(isinstance(s, dict) for s in session_dicts)
        assert all('user_id' in s for s in session_dicts)
        assert all('store_name' in s for s in session_dicts)

    def test_get_sessions_empty_result(self, db_manager):
        """Test retrieving sessions when none exist."""
        sessions = db_manager.get_sessions("nonexistent_user")
        assert len(sessions) == 0


class TestMonthlyStatistics:
    """Test monthly statistics functionality."""

    def create_monthly_test_data(self, db_manager):
        """Create test data for monthly statistics."""
        sessions_data = [
            # January 2024 - 3 sessions, 2 completed
            (datetime(2024, 1, 15), 10000, 15000, 20000),  # +5000 profit
            (datetime(2024, 1, 16), 12000, 18000, 15000),  # -3000 loss
            (datetime(2024, 1, 17), 8000, None, None),     # Incomplete

            # February 2024 - 2 sessions, both completed
            (datetime(2024, 2, 10), 15000, 20000, 25000),  # +5000 profit
            (datetime(2024, 2, 11), 10000, 15000, 12000),  # -3000 loss
        ]

        for i, (date, initial, final, return_amt) in enumerate(sessions_data):
            session = GameSession(
                user_id="test_user",
                date=date,
                start_time=date.replace(hour=10),
                store_name=f"テストホール{i+1}",
                machine_name="CR花の慶次",
                initial_investment=initial
            )

            if final is not None and return_amt is not None:
                session.complete_session(
                    end_time=date.replace(hour=12),
                    final_investment=final,
                    return_amount=return_amt
                )

            db_manager.create_session(session)

    def test_get_monthly_stats_with_data(self, db_manager):
        """Test monthly statistics calculation with data."""
        self.create_monthly_test_data(db_manager)

        # Get January 2024 stats
        stats = db_manager.get_monthly_stats("test_user", 2024, 1)

        assert stats['total_sessions'] == 3
        assert stats['completed_sessions'] == 2
        assert stats['total_investment'] == 33000  # 15000 + 18000
        assert stats['total_return'] == 35000      # 20000 + 15000
        assert stats['total_profit'] == 2000       # 5000 + (-3000)
        assert stats['winning_sessions'] == 1      # Only first session won
        assert stats['win_rate'] == 50.0           # 1/2 * 100
        assert stats['avg_investment'] == 16500    # 33000/2
        assert stats['avg_profit'] == 1000         # 2000/2

    def test_get_monthly_stats_no_data(self, db_manager):
        """Test monthly statistics with no data."""
        stats = db_manager.get_monthly_stats("test_user", 2024, 12)

        assert stats['total_sessions'] == 0
        assert stats['completed_sessions'] == 0
        assert stats['total_investment'] == 0
        assert stats['total_return'] == 0
        assert stats['total_profit'] == 0
        assert stats['winning_sessions'] == 0
        assert stats['win_rate'] == 0
        assert stats['avg_investment'] == 0
        assert stats['avg_profit'] == 0

    def test_get_monthly_stats_different_months(self, db_manager):
        """Test monthly statistics for different months."""
        self.create_monthly_test_data(db_manager)

        # Get February 2024 stats
        stats = db_manager.get_monthly_stats("test_user", 2024, 2)

        assert stats['total_sessions'] == 2
        assert stats['completed_sessions'] == 2
        assert stats['total_profit'] == 2000  # 5000 + (-3000)


class TestDataIntegrity:
    """Test data integrity checking functionality."""

    def test_check_data_integrity_clean_data(self, db_manager, completed_session):
        """Test data integrity check with clean data."""
        db_manager.create_session(completed_session)

        integrity_result = db_manager.check_data_integrity()

        assert integrity_result['total_records'] == 1
        assert integrity_result['incomplete_completed'] == 0
        assert integrity_result['profit_mismatch'] == 0
        assert integrity_result['invalid_investment'] == 0
        assert integrity_result['has_issues'] is False

    def test_check_data_integrity_with_issues(self, db_manager, temp_db):
        """Test data integrity check with problematic data."""
        # Create a session first
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        session_id = db_manager.create_session(session)

        # Manually corrupt data to test integrity checking
        with sqlite3.connect(temp_db) as conn:
            # Create a completed session with missing final_investment
            conn.execute("""
                UPDATE game_sessions 
                SET is_completed = 1, final_investment = NULL, return_amount = 20000
                WHERE id = ?
            """, (session_id,))
            conn.commit()

        integrity_result = db_manager.check_data_integrity()

        assert integrity_result['total_records'] == 1
        assert integrity_result['incomplete_completed'] == 1
        assert integrity_result['has_issues'] is True

    def test_database_info(self, db_manager, sample_session):
        """Test database information retrieval."""
        # Create a session
        db_manager.create_session(sample_session)

        db_info = db_manager.get_database_info()

        assert 'schema_version' in db_info
        assert 'tables' in db_info
        assert 'indexes' in db_info
        assert 'total_sessions' in db_info
        assert 'completed_sessions' in db_info
        assert 'database_path' in db_info
        assert 'database_size' in db_info

        assert db_info['schema_version'] == DatabaseManager.CURRENT_SCHEMA_VERSION
        assert 'game_sessions' in db_info['tables']
        assert db_info['total_sessions'] == 1
        assert db_info['completed_sessions'] == 0


class TestTransactionManagement:
    """Test transaction management and error handling."""

    def test_transaction_rollback_on_error(self, db_manager, temp_db):
        """Test that transactions are rolled back on errors."""
        # Create a valid session first
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        session_id = db_manager.create_session(session)

        # Count sessions before error
        sessions_before = db_manager.get_sessions("test_user")
        count_before = len(sessions_before)

        # Try to create an invalid session (should fail and rollback)
        try:
            invalid_session = GameSession(
                user_id="",  # This will cause validation error
                date=datetime(2024, 1, 16),
                start_time=datetime(2024, 1, 16, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            db_manager.create_session(invalid_session)
        except ValidationError:
            pass  # Expected error

        # Count sessions after error
        sessions_after = db_manager.get_sessions("test_user")
        count_after = len(sessions_after)

        # Should be the same (no partial data committed)
        assert count_before == count_after

    def test_connection_cleanup(self, db_manager):
        """Test that database connections are properly cleaned up."""
        # This test ensures connections are closed properly
        # by performing multiple operations
        for i in range(10):
            session = GameSession(
                user_id=f"test_user_{i}",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            db_manager.create_session(session)

        # If connections aren't cleaned up properly, this would fail
        sessions = db_manager.get_sessions("test_user_5")
        assert len(sessions) == 1


class TestDatabaseReset:
    """Test database reset functionality."""

    def test_reset_database(self, db_manager, sample_session):
        """Test database reset functionality."""
        # Create some data
        db_manager.create_session(sample_session)

        # Verify data exists
        sessions_before = db_manager.get_sessions("test_user_123")
        assert len(sessions_before) == 1

        # Reset database
        db_manager.reset_database()

        # Verify data is gone
        sessions_after = db_manager.get_sessions("test_user_123")
        assert len(sessions_after) == 0

        # Verify schema is still intact
        db_info = db_manager.get_database_info()
        assert 'game_sessions' in db_info['tables']
        assert db_info['schema_version'] == DatabaseManager.CURRENT_SCHEMA_VERSION


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
