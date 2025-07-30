"""
Database management for the Pachinko Revenue Calculator application.
"""

import sqlite3
import os
import logging
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    from psycopg2 import pool
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

from .models_fixed import GameSession, ValidationError
from .error_handler import handle_error, ErrorCategory, ErrorSeverity
from .config import get_config


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class DatabaseManager:
    """
    Manages database operations for the Pachinko Revenue Calculator.

    Handles both SQLite (development) and PostgreSQL (production) database connections,
    table creation, and CRUD operations for game sessions with proper error handling
    and transaction management.
    """

    # Database schema version for migration tracking
    CURRENT_SCHEMA_VERSION = 1

    def __init__(self, db_path: str = None, encryption_manager=None, config=None):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file (deprecated, use config)
            encryption_manager: Optional encryption manager for data security
            config: Configuration object with database settings
        """
        self.config = config or get_config()
        self.db_config = self.config.get_database_config()
        self.encryption_manager = encryption_manager
        self.logger = logging.getLogger(__name__)

        # Database type and connection settings
        self.db_type = self.db_config['type']
        self.connection_pool = None

        # Backward compatibility
        if db_path and self.db_type == 'sqlite':
            self.db_config['path'] = db_path

        self._initialize_database()

    def set_encryption_manager(self, encryption_manager):
        """
        Set the encryption manager for data security.

        Args:
            encryption_manager: Authentication manager with encryption capabilities
        """
        self.encryption_manager = encryption_manager
        self.logger.info("Encryption manager set for database operations")

    def _initialize_database(self) -> None:
        """Initialize the database and create tables if they don't exist."""
        try:
            with self._get_connection() as conn:
                # Check if this is a new database or needs migration
                current_version = self._get_schema_version(conn)

                if current_version == 0:
                    # New database - create all tables and indexes
                    self._create_schema_version_table(conn)
                    self._create_tables(conn)
                    self._create_indexes(conn)
                    self._set_schema_version(conn, self.CURRENT_SCHEMA_VERSION)
                    self.logger.info("New database initialized successfully")
                elif current_version < self.CURRENT_SCHEMA_VERSION:
                    # Existing database - run migrations
                    self._run_migrations(conn, current_version)
                    self.logger.info(
                        f"Database migrated from version {current_version} to {self.CURRENT_SCHEMA_VERSION}")
                else:
                    # Database is up to date
                    self.logger.info("Database is up to date")

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            handle_error(
                e, {'operation': 'database_initialization', 'db_path': self.db_path})
            raise DatabaseError(f"Database initialization failed: {e}")

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with automatic cleanup.

        Yields:
            Database connection (sqlite3.Connection or psycopg2.Connection)
        """
        conn = None
        try:
            if self.db_type == 'postgresql':
                conn = self._get_postgresql_connection()
            else:
                conn = self._get_sqlite_connection()

            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Database connection failed: {e}")
        finally:
            if conn:
                if self.db_type == 'postgresql' and self.connection_pool:
                    # Return connection to pool
                    self.connection_pool.putconn(conn)
                elif conn:
                    conn.close()

    def _get_sqlite_connection(self):
        """Get SQLite database connection."""
        db_path = self.db_config.get('path', 'pachinko_data.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def _get_postgresql_connection(self):
        """Get PostgreSQL database connection."""
        if not POSTGRESQL_AVAILABLE:
            raise DatabaseError(
                "PostgreSQL support not available. Install psycopg2-binary.")

        if self.connection_pool is None:
            self._initialize_connection_pool()

        try:
            conn = self.connection_pool.getconn()
            # Set up cursor factory for dict-like access
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            return conn
        except Exception as e:
            self.logger.error(f"Failed to get PostgreSQL connection: {e}")
            raise DatabaseError(f"PostgreSQL connection failed: {e}")

    def _initialize_connection_pool(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.db_config.get('pool_size', 10),
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password'],
                sslmode=self.db_config.get('ssl_mode', 'require')
            )
            self.logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize connection pool: {e}")
            raise DatabaseError(f"Connection pool initialization failed: {e}")

    def _create_schema_version_table(self, conn) -> None:
        """
        Create the schema_version table for migration tracking.

        Args:
            conn: Database connection
        """
        if self.db_type == 'postgresql':
            create_version_table_sql = """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        else:
            create_version_table_sql = """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

        try:
            cursor = conn.cursor()
            cursor.execute(create_version_table_sql)
            conn.commit()
            self.logger.info("Schema version table created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create schema version table: {e}")
            raise DatabaseError(f"Schema version table creation failed: {e}")

    def _create_tables(self, conn) -> None:
        """
        Create the game_sessions table with complete schema.

        Args:
            conn: Database connection
        """
        if self.db_type == 'postgresql':
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS game_sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
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
                
                -- Constraints for data integrity
                CHECK (initial_investment >= 0),
                CHECK (final_investment >= 0 OR final_investment IS NULL),
                CHECK (return_amount >= 0 OR return_amount IS NULL),
                CHECK (final_investment >= initial_investment OR final_investment IS NULL),
                CHECK (is_completed = FALSE OR (is_completed = TRUE AND end_time IS NOT NULL AND final_investment IS NOT NULL AND return_amount IS NOT NULL))
            );
            """
        else:
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
                
                -- Constraints for data integrity
                CHECK (initial_investment >= 0),
                CHECK (final_investment >= 0 OR final_investment IS NULL),
                CHECK (return_amount >= 0 OR return_amount IS NULL),
                CHECK (final_investment >= initial_investment OR final_investment IS NULL),
                CHECK (is_completed = 0 OR (is_completed = 1 AND end_time IS NOT NULL AND final_investment IS NOT NULL AND return_amount IS NOT NULL))
            );
            """

        try:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            self.logger.info("Tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")

    def _create_indexes(self, conn) -> None:
        """
        Create indexes for performance optimization as specified in requirements.

        Creates indexes for:
        - user_date: For efficient date-based queries (Requirement 2.1, 3.1)
        - user_month: For monthly statistics (Requirement 3.1)
        - Additional performance indexes

        Args:
            conn: Database connection
        """
        if self.db_type == 'postgresql':
            indexes = [
                # Primary performance indexes as specified in requirements
                "CREATE INDEX IF NOT EXISTS idx_user_date ON game_sessions(user_id, date);",
                "CREATE INDEX IF NOT EXISTS idx_user_month ON game_sessions(user_id, EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date));",

                # Additional indexes for query optimization
                "CREATE INDEX IF NOT EXISTS idx_user_completed ON game_sessions(user_id, is_completed);",
                "CREATE INDEX IF NOT EXISTS idx_date_desc ON game_sessions(date DESC);",
                "CREATE INDEX IF NOT EXISTS idx_user_machine ON game_sessions(user_id, machine_name);",
                "CREATE INDEX IF NOT EXISTS idx_user_store ON game_sessions(user_id, store_name);",
                "CREATE INDEX IF NOT EXISTS idx_created_at ON game_sessions(created_at);"
            ]
        else:
            indexes = [
                # Primary performance indexes as specified in requirements
                "CREATE INDEX IF NOT EXISTS idx_user_date ON game_sessions(user_id, date);",
                "CREATE INDEX IF NOT EXISTS idx_user_month ON game_sessions(user_id, strftime('%Y-%m', date));",

                # Additional indexes for query optimization
                "CREATE INDEX IF NOT EXISTS idx_user_completed ON game_sessions(user_id, is_completed);",
                "CREATE INDEX IF NOT EXISTS idx_date_desc ON game_sessions(date DESC);",
                "CREATE INDEX IF NOT EXISTS idx_user_machine ON game_sessions(user_id, machine_name);",
                "CREATE INDEX IF NOT EXISTS idx_user_store ON game_sessions(user_id, store_name);",
                "CREATE INDEX IF NOT EXISTS idx_created_at ON game_sessions(created_at);"
            ]

        try:
            cursor = conn.cursor()
            for index_sql in indexes:
                cursor.execute(index_sql)
            conn.commit()
            self.logger.info("Performance indexes created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create indexes: {e}")
            raise DatabaseError(f"Index creation failed: {e}")

    def create_session(self, session: GameSession) -> int:
        """
        Create a new game session in the database.

        Args:
            session: GameSession object to create

        Returns:
            int: ID of the created session

        Raises:
            DatabaseError: If session creation fails
            ValidationError: If session data is invalid
        """
        try:
            # Validate the session before saving
            session.validate()

            # Prepare data for encryption if encryption manager is available
            store_name = session.store_name
            machine_name = session.machine_name

            if self.encryption_manager:
                # Encrypt sensitive data
                session_data = {
                    'store_name': session.store_name,
                    'machine_name': session.machine_name
                }
                encrypted_data = self.encryption_manager.encrypt_user_data(
                    session_data)
                store_name = encrypted_data['store_name']
                machine_name = encrypted_data['machine_name']

            if self.db_type == 'postgresql':
                insert_sql = """
                INSERT INTO game_sessions (
                    user_id, date, start_time, end_time, store_name, machine_name,
                    initial_investment, final_investment, return_amount, profit,
                    is_completed, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """
            else:
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
                store_name,
                machine_name,
                session.initial_investment,
                session.final_investment,
                session.return_amount,
                session.profit,
                session.is_completed,
                session.created_at.isoformat(),
                session.updated_at.isoformat()
            )

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_sql, values)

                if self.db_type == 'postgresql':
                    session_id = cursor.fetchone()[0]
                else:
                    session_id = cursor.lastrowid

                conn.commit()

                # Update the session object with the new ID
                session.id = session_id

                self.logger.info(f"Session created with ID: {session_id}")
                return session_id

        except ValidationError:
            raise  # Re-raise validation errors as-is
        except sqlite3.Error as e:
            self.logger.error(f"Failed to create session: {e}")
            raise DatabaseError(f"Session creation failed: {e}")

    def update_session(self, session_id: int, session: GameSession) -> bool:
        """
        Update an existing game session.

        Args:
            session_id: ID of the session to update
            session: Updated GameSession object

        Returns:
            bool: True if update was successful

        Raises:
            DatabaseError: If update fails
            ValidationError: If session data is invalid
        """
        try:
            # Validate the session before updating
            session.validate()

            # Prepare data for encryption if encryption manager is available
            store_name = session.store_name
            machine_name = session.machine_name

            if self.encryption_manager:
                # Encrypt sensitive data
                session_data = {
                    'store_name': session.store_name,
                    'machine_name': session.machine_name
                }
                encrypted_data = self.encryption_manager.encrypt_user_data(
                    session_data)
                store_name = encrypted_data['store_name']
                machine_name = encrypted_data['machine_name']

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
                store_name,
                machine_name,
                session.initial_investment,
                session.final_investment,
                session.return_amount,
                session.profit,
                session.is_completed,
                datetime.now().isoformat(),
                session_id
            )

            with self._get_connection() as conn:
                cursor = conn.execute(update_sql, values)
                conn.commit()

                if cursor.rowcount == 0:
                    raise DatabaseError(
                        f"Session with ID {session_id} not found")

                self.logger.info(f"Session {session_id} updated successfully")
                return True

        except ValidationError:
            raise  # Re-raise validation errors as-is
        except sqlite3.Error as e:
            self.logger.error(f"Failed to update session {session_id}: {e}")
            raise DatabaseError(f"Session update failed: {e}")

    def get_session(self, session_id: int) -> Optional[GameSession]:
        """
        Retrieve a single game session by ID.

        Args:
            session_id: ID of the session to retrieve

        Returns:
            GameSession or None if not found

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            select_sql = "SELECT * FROM game_sessions WHERE id = ?"

            with self._get_connection() as conn:
                cursor = conn.execute(select_sql, (session_id,))
                row = cursor.fetchone()

                if row:
                    return self._row_to_session(row)
                return None

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get session {session_id}: {e}")
            raise DatabaseError(f"Session retrieval failed: {e}")

    def get_sessions(self, user_id: str, date_range: Optional[Tuple[datetime, datetime]] = None,
                     limit: Optional[int] = None, offset: int = 0) -> List[GameSession]:
        """
        Retrieve game sessions for a user with optional filtering.

        Args:
            user_id: User ID to filter by
            date_range: Optional tuple of (start_date, end_date) for filtering
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of GameSession objects

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            base_sql = "SELECT * FROM game_sessions WHERE user_id = ?"
            params = [user_id]

            # Add date range filtering if provided
            if date_range:
                start_date, end_date = date_range
                base_sql += " AND date BETWEEN ? AND ?"
                params.extend([start_date.isoformat(), end_date.isoformat()])

            # Add ordering
            base_sql += " ORDER BY date DESC, start_time DESC"

            # Add pagination
            if limit:
                base_sql += " LIMIT ?"
                params.append(limit)

            if offset > 0:
                base_sql += " OFFSET ?"
                params.append(offset)

            with self._get_connection() as conn:
                cursor = conn.execute(base_sql, params)
                rows = cursor.fetchall()

                sessions = [self._row_to_session(row) for row in rows]
                self.logger.info(
                    f"Retrieved {len(sessions)} sessions for user {user_id}")
                return sessions

        except sqlite3.Error as e:
            self.logger.error(
                f"Failed to get sessions for user {user_id}: {e}")
            raise DatabaseError(f"Sessions retrieval failed: {e}")

    def get_sessions_as_dict(self, user_id: str, date_range: Optional[Tuple[datetime, datetime]] = None,
                             limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve game sessions for a user as dictionaries with optional filtering.

        Args:
            user_id: User ID to filter by
            date_range: Optional tuple of (start_date, end_date) for filtering
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip

        Returns:
            List of session dictionaries

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            sessions = self.get_sessions(user_id, date_range, limit, offset)
            return [session.to_dict() for session in sessions]
        except Exception as e:
            self.logger.error(
                f"Failed to get sessions as dict for user {user_id}: {e}")
            raise DatabaseError(f"Sessions retrieval as dict failed: {e}")

    def delete_session(self, session_id: int) -> bool:
        """
        Delete a game session.

        Args:
            session_id: ID of the session to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            DatabaseError: If deletion fails
        """
        try:
            delete_sql = "DELETE FROM game_sessions WHERE id = ?"

            with self._get_connection() as conn:
                cursor = conn.execute(delete_sql, (session_id,))
                conn.commit()

                if cursor.rowcount == 0:
                    raise DatabaseError(
                        f"Session with ID {session_id} not found")

                self.logger.info(f"Session {session_id} deleted successfully")
                return True

        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete session {session_id}: {e}")
            raise DatabaseError(f"Session deletion failed: {e}")

    def get_monthly_stats(self, user_id: str, year: int, month: int) -> Dict[str, Any]:
        """
        Get monthly statistics for a user.

        Args:
            user_id: User ID
            year: Year to get stats for
            month: Month to get stats for (1-12)

        Returns:
            Dictionary containing monthly statistics

        Raises:
            DatabaseError: If retrieval fails
        """
        try:
            if self.db_type == 'postgresql':
                stats_sql = """
                SELECT 
                    COUNT(*) as total_sessions,
                    COUNT(CASE WHEN is_completed = TRUE THEN 1 END) as completed_sessions,
                    SUM(CASE WHEN is_completed = TRUE THEN final_investment ELSE 0 END) as total_investment,
                    SUM(CASE WHEN is_completed = TRUE THEN return_amount ELSE 0 END) as total_return,
                    SUM(CASE WHEN is_completed = TRUE THEN profit ELSE 0 END) as total_profit,
                    COUNT(CASE WHEN is_completed = TRUE AND profit > 0 THEN 1 END) as winning_sessions,
                    AVG(CASE WHEN is_completed = TRUE THEN final_investment END) as avg_investment,
                    AVG(CASE WHEN is_completed = TRUE THEN profit END) as avg_profit
                FROM game_sessions 
                WHERE user_id = %s AND EXTRACT(YEAR FROM date) = %s AND EXTRACT(MONTH FROM date) = %s
                """
                params = (user_id, year, month)
            else:
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
                params = (user_id, month_str)

            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(stats_sql, params)
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

        except Exception as e:
            self.logger.error(f"Failed to get monthly stats: {e}")
            raise DatabaseError(f"Monthly stats retrieval failed: {e}")

    def _row_to_session(self, row: sqlite3.Row) -> GameSession:
        """
        Convert a database row to a GameSession object.

        Args:
            row: Database row

        Returns:
            GameSession object
        """
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

        # Decrypt sensitive data if encryption manager is available
        if self.encryption_manager:
            try:
                # Prepare data for decryption (add encryption flags)
                encrypted_data = {
                    'store_name': data['store_name'],
                    'machine_name': data['machine_name'],
                    'store_name_encrypted': True,
                    'machine_name_encrypted': True
                }

                # Decrypt the data
                decrypted_data = self.encryption_manager.decrypt_user_data(
                    encrypted_data)

                # Update the data with decrypted values
                data['store_name'] = decrypted_data['store_name']
                data['machine_name'] = decrypted_data['machine_name']

            except Exception as e:
                # If decryption fails, assume data is not encrypted (backward compatibility)
                self.logger.warning(
                    f"Failed to decrypt session data (ID: {data['id']}): {e}")

        return GameSession.from_dict(data)

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics dictionary."""
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

    def check_data_integrity(self) -> Dict[str, Any]:
        """
        Check database data integrity.

        Returns:
            Dictionary with integrity check results
        """
        try:
            integrity_sql = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN is_completed = 1 AND (final_investment IS NULL OR return_amount IS NULL) THEN 1 END) as incomplete_completed,
                COUNT(CASE WHEN is_completed = 1 AND profit != (return_amount - final_investment) THEN 1 END) as profit_mismatch,
                COUNT(CASE WHEN final_investment < initial_investment THEN 1 END) as invalid_investment
            FROM game_sessions
            """

            with self._get_connection() as conn:
                cursor = conn.execute(integrity_sql)
                row = cursor.fetchone()

                return {
                    'total_records': row['total_records'],
                    'incomplete_completed': row['incomplete_completed'],
                    'profit_mismatch': row['profit_mismatch'],
                    'invalid_investment': row['invalid_investment'],
                    'has_issues': (row['incomplete_completed'] + row['profit_mismatch'] + row['invalid_investment']) > 0
                }

        except sqlite3.Error as e:
            self.logger.error(f"Data integrity check failed: {e}")
            raise DatabaseError(f"Data integrity check failed: {e}")

    def _get_schema_version(self, conn) -> int:
        """
        Get the current schema version from the database.

        Args:
            conn: Database connection

        Returns:
            int: Current schema version (0 if no version table exists)
        """
        try:
            cursor = conn.cursor()

            if self.db_type == 'postgresql':
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'schema_version'
                    );
                """)
                if not cursor.fetchone()[0]:
                    return 0  # No version table means new database
            else:
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';")
                if not cursor.fetchone():
                    return 0  # No version table means new database

            cursor.execute("SELECT MAX(version) FROM schema_version;")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0

        except Exception:
            return 0  # Assume new database on any error

    def _set_schema_version(self, conn, version: int) -> None:
        """
        Set the schema version in the database.

        Args:
            conn: Database connection
            version: Schema version to set
        """
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (%s);" if self.db_type == 'postgresql' else "INSERT INTO schema_version (version) VALUES (?);",
                (version,))
            conn.commit()
            self.logger.info(f"Schema version set to {version}")
        except Exception as e:
            self.logger.error(f"Failed to set schema version: {e}")
            raise DatabaseError(f"Schema version update failed: {e}")

    def _run_migrations(self, conn: sqlite3.Connection, from_version: int) -> None:
        """
        Run database migrations from the current version to the latest.

        Args:
            conn: Database connection
            from_version: Current schema version
        """
        try:
            # Migration logic for future schema changes
            # Currently at version 1, so no migrations needed yet

            if from_version < 1:
                # Future migration logic would go here
                # For now, we're at the initial version
                pass

            # Update to current version
            self._set_schema_version(conn, self.CURRENT_SCHEMA_VERSION)

        except Exception as e:
            self.logger.error(f"Migration failed: {e}")
            raise DatabaseError(f"Database migration failed: {e}")

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database structure and status.

        Returns:
            Dictionary containing database information
        """
        try:
            with self._get_connection() as conn:
                # Get schema version
                version = self._get_schema_version(conn)

                # Get table information
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name;
                """)
                tables = [row[0] for row in cursor.fetchall()]

                # Get index information
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name;
                """)
                indexes = [row[0] for row in cursor.fetchall()]

                # Get record counts
                cursor = conn.execute("SELECT COUNT(*) FROM game_sessions;")
                total_sessions = cursor.fetchone()[0]

                cursor = conn.execute(
                    "SELECT COUNT(*) FROM game_sessions WHERE is_completed = 1;")
                completed_sessions = cursor.fetchone()[0]

                return {
                    'schema_version': version,
                    'tables': tables,
                    'indexes': indexes,
                    'total_sessions': total_sessions,
                    'completed_sessions': completed_sessions,
                    'database_path': self.db_path,
                    'database_size': os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                }

        except sqlite3.Error as e:
            self.logger.error(f"Failed to get database info: {e}")
            raise DatabaseError(f"Database info retrieval failed: {e}")

    def reset_database(self) -> None:
        """
        Reset the database by dropping all tables and recreating them.

        WARNING: This will delete all data!
        """
        try:
            with self._get_connection() as conn:
                # Get all table names
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%';
                """)
                tables = [row[0] for row in cursor.fetchall()]

                # Drop all tables
                for table in tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table};")

                # Recreate schema
                self._create_schema_version_table(conn)
                self._create_tables(conn)
                self._create_indexes(conn)
                self._set_schema_version(conn, self.CURRENT_SCHEMA_VERSION)

                conn.commit()
                self.logger.info("Database reset successfully")

        except sqlite3.Error as e:
            self.logger.error(f"Failed to reset database: {e}")
            raise DatabaseError(f"Database reset failed: {e}")
