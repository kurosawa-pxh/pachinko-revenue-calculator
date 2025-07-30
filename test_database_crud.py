#!/usr/bin/env python3
"""
Comprehensive test suite for DatabaseManager CRUD operations and data integrity.
Tests database operations without circular import issues.
"""

from src.models import GameSession, ValidationError
import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


class SimpleDatabaseManager:
    """
    Simplified database manager for testing without circular imports.
    Contains core CRUD functionality from the original DatabaseManager.
    """

    def __init__(self, db_path: str = "test.db"):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database and create tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            self._create_tables(conn)
            self._create_indexes(conn)

    def _create_tables(self, conn):
        """Create the game_sessions table."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS game_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            date DATE NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            store_name TEXT NOT NULL,
            machine_name TEXT NOT NULL,
            initial_investment INTEGER NOT NULL,
            final_investment INTEGER,
            return_amount INTEGER,
            profit INTEGER,
            is_completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            CHECK (initial_investment >= 0),
            CHECK (final_investment >= 0 OR final_investment IS NULL),
            CHECK (return_amount >= 0 OR return_amount IS NULL),
            CHECK (final_investment >= initial_investment OR final_investment IS NULL)
        );
        """
        conn.execute(create_table_sql)
        conn.commit()

    def _create_indexes(self, conn):
        """Create performance indexes."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_user_date ON game_sessions(user_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_user_month ON game_sessions(user_id, strftime('%Y-%m', date));",
        ]
        for index_sql in indexes:
            conn.execute(index_sql)
        conn.commit()

    def create_session(self, session: GameSession) -> int:
        """Create a new game session."""
        session.validate()

        insert_sql = """
        INSERT INTO game_sessions (
            user_id, date, start_time, end_time, store_name, machine_name,
            initial_investment, final_investment, return_amount, profit,
            is_completed, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            session.user_id,
            session.date.isoformat(),
            session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
            session.store_name,
            session.machine_name,
            session.initial_investment,
            session.final_investment,
            session.return_amount,
            session.profit,
            session.is_completed,
            session.created_at.isoformat(),
            session.updated_at.isoformat()
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(insert_sql, values)
            session_id = cursor.lastrowid
            conn.commit()
            session.id = session_id
            return session_id

    def get_session(self, session_id: int):
        """Retrieve a session by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM game_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()

            if row:
                return self._row_to_session(row)
            return None

    def update_session(self, session_id: int, session: GameSession) -> bool:
        """Update an existing session."""
        session.validate()

        update_sql = """
        UPDATE game_sessions SET
            user_id = ?, date = ?, start_time = ?, end_time = ?,
            store_name = ?, machine_name = ?, initial_investment = ?,
            final_investment = ?, return_amount = ?, profit = ?,
            is_completed = ?, updated_at = ?
        WHERE id = ?
        """

        values = (
            session.user_id,
            session.date.isoformat(),
            session.start_time.isoformat(),
            session.end_time.isoformat() if session.end_time else None,
            session.store_name,
            session.machine_name,
            session.initial_investment,
            session.final_investment,
            session.return_amount,
            session.profit,
            session.is_completed,
            datetime.now().isoformat(),
            session_id
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(update_sql, values)
            conn.commit()

            if cursor.rowcount == 0:
                raise Exception(f"Session with ID {session_id} not found")
            return True

    def delete_session(self, session_id: int) -> bool:
        """Delete a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM game_sessions WHERE id = ?", (session_id,))
            conn.commit()

            if cursor.rowcount == 0:
                raise Exception(f"Session with ID {session_id} not found")
            return True

    def get_sessions(self, user_id: str, date_range=None, limit=None, offset=0):
        """Get sessions for a user."""
        base_sql = "SELECT * FROM game_sessions WHERE user_id = ?"
        params = [user_id]

        if date_range:
            start_date, end_date = date_range
            base_sql += " AND date BETWEEN ? AND ?"
            params.extend([start_date.isoformat(), end_date.isoformat()])

        base_sql += " ORDER BY date DESC, start_time DESC"

        if limit:
            base_sql += " LIMIT ?"
            params.append(limit)

        if offset > 0:
            base_sql += " OFFSET ?"
            params.append(offset)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(base_sql, params)
            rows = cursor.fetchall()
            return [self._row_to_session(row) for row in rows]

    def get_monthly_stats(self, user_id: str, year: int, month: int):
        """Get monthly statistics."""
        stats_sql = """
        SELECT 
            COUNT(*) as total_sessions,
            COUNT(CASE WHEN is_completed = 1 THEN 1 END) as completed_sessions,
            SUM(CASE WHEN is_completed = 1 THEN final_investment ELSE 0 END) as total_investment,
            SUM(CASE WHEN is_completed = 1 THEN return_amount ELSE 0 END) as total_return,
            SUM(CASE WHEN is_completed = 1 THEN profit ELSE 0 END) as total_profit,
            COUNT(CASE WHEN is_completed = 1 AND profit > 0 THEN 1 END) as winning_sessions,
            AVG(CASE WHEN is_completed = 1 THEN final_investment END) as avg_investment,
            AVG(CASE WHEN is_completed = 1 THEN profit END) as avg_profit
        FROM game_sessions 
        WHERE user_id = ? AND strftime('%Y-%m', date) = ?
        """

        month_str = f"{year:04d}-{month:02d}"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(stats_sql, (user_id, month_str))
            row = cursor.fetchone()

            if row:
                completed = row['completed_sessions'] or 0
                winning = row['winning_sessions'] or 0

                return {
                    'total_sessions': row['total_sessions'] or 0,
                    'completed_sessions': completed,
                    'total_investment': row['total_investment'] or 0,
                    'total_return': row['total_return'] or 0,
                    'total_profit': row['total_profit'] or 0,
                    'winning_sessions': winning,
                    'win_rate': (winning / completed * 100) if completed > 0 else 0,
                    'avg_investment': row['avg_investment'] or 0,
                    'avg_profit': row['avg_profit'] or 0
                }

            return self._empty_stats()

    def check_data_integrity(self):
        """Check database data integrity."""
        integrity_sql = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN is_completed = 1 AND (final_investment IS NULL OR return_amount IS NULL) THEN 1 END) as incomplete_completed,
            COUNT(CASE WHEN is_completed = 1 AND profit != (return_amount - final_investment) THEN 1 END) as profit_mismatch,
            COUNT(CASE WHEN final_investment < initial_investment THEN 1 END) as invalid_investment
        FROM game_sessions
        """

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(integrity_sql)
            row = cursor.fetchone()

            return {
                'total_records': row['total_records'],
                'incomplete_completed': row['incomplete_completed'],
                'profit_mismatch': row['profit_mismatch'],
                'invalid_investment': row['invalid_investment'],
                'has_issues': (row['incomplete_completed'] + row['profit_mismatch'] + row['invalid_investment']) > 0
            }

    def _row_to_session(self, row):
        """Convert database row to GameSession."""
        data = {
            'id': row['id'],
            'user_id': row['user_id'],
            'date': row['date'],
            'start_time': row['start_time'],
            'end_time': row['end_time'],
            'store_name': row['store_name'],
            'machine_name': row['machine_name'],
            'initial_investment': row['initial_investment'],
            'final_investment': row['final_investment'],
            'return_amount': row['return_amount'],
            'profit': row['profit'],
            'is_completed': bool(row['is_completed']),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }
        return GameSession.from_dict(data)

    def _empty_stats(self):
        """Return empty statistics."""
        return {
            'total_sessions': 0,
            'completed_sessions': 0,
            'total_investment': 0,
            'total_return': 0,
            'total_profit': 0,
            'winning_sessions': 0,
            'win_rate': 0,
            'avg_investment': 0,
            'avg_profit': 0
        }


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
    return SimpleDatabaseManager(temp_db)


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
        db_manager = SimpleDatabaseManager(temp_db)

        # Check that database file was created
        assert os.path.exists(temp_db)

        # Check that tables were created
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='game_sessions'
            """)
            assert cursor.fetchone() is not None

    def test_indexes_creation(self, temp_db):
        """Test that performance indexes are created."""
        db_manager = SimpleDatabaseManager(temp_db)

        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]

            # Check required indexes exist
            required_indexes = ['idx_user_date', 'idx_user_month']

            for required_index in required_indexes:
                assert required_index in indexes


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
        session_id = db_manager.create_session(sample_session)

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
        session_id = db_manager.create_session(sample_session)

        sample_session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )

        result = db_manager.update_session(session_id, sample_session)
        assert result is True

        updated_session = db_manager.get_session(session_id)
        assert updated_session.is_completed is True
        assert updated_session.final_investment == 15000
        assert updated_session.return_amount == 20000
        assert updated_session.profit == 5000

    def test_update_session_not_found(self, db_manager, sample_session):
        """Test updating non-existent session."""
        with pytest.raises(Exception):
            db_manager.update_session(99999, sample_session)

    def test_delete_session_success(self, db_manager, sample_session):
        """Test successful session deletion."""
        session_id = db_manager.create_session(sample_session)

        result = db_manager.delete_session(session_id)
        assert result is True

        deleted_session = db_manager.get_session(session_id)
        assert deleted_session is None

    def test_delete_session_not_found(self, db_manager):
        """Test deleting non-existent session."""
        with pytest.raises(Exception):
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
        assert retrieved_sessions[0].date >= retrieved_sessions[1].date
        assert retrieved_sessions[1].date >= retrieved_sessions[2].date

    def test_get_sessions_with_date_range(self, db_manager):
        """Test retrieving sessions with date range filtering."""
        sessions = self.create_multiple_sessions(db_manager, "test_user", 5)

        start_date = datetime(2024, 1, 16)
        end_date = datetime(2024, 1, 18)

        filtered_sessions = db_manager.get_sessions(
            "test_user",
            date_range=(start_date, end_date)
        )

        assert len(filtered_sessions) == 3
        for session in filtered_sessions:
            assert start_date.date() <= session.date.date() <= end_date.date()

    def test_get_sessions_with_pagination(self, db_manager):
        """Test retrieving sessions with pagination."""
        sessions = self.create_multiple_sessions(db_manager, "test_user", 10)

        page1 = db_manager.get_sessions("test_user", limit=3, offset=0)
        assert len(page1) == 3

        page2 = db_manager.get_sessions("test_user", limit=3, offset=3)
        assert len(page2) == 3

        page1_ids = {s.id for s in page1}
        page2_ids = {s.id for s in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_sessions_empty_result(self, db_manager):
        """Test retrieving sessions when none exist."""
        sessions = db_manager.get_sessions("nonexistent_user")
        assert len(sessions) == 0


class TestMonthlyStatistics:
    """Test monthly statistics functionality."""

    def create_monthly_test_data(self, db_manager):
        """Create test data for monthly statistics."""
        sessions_data = [
            (datetime(2024, 1, 15), 10000, 15000, 20000),  # +5000 profit
            (datetime(2024, 1, 16), 12000, 18000, 15000),  # -3000 loss
            (datetime(2024, 1, 17), 8000, None, None),     # Incomplete
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


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
