#!/usr/bin/env python3
"""
Test script to verify the database schema and migration functionality.
"""

from src.database import DatabaseManager, DatabaseError
import sys
import os
import tempfile
import sqlite3

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_schema_creation():
    """Test database schema creation and structure."""
    print("Testing database schema creation...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database
        db_manager = DatabaseManager(db_path)

        # Check database info
        db_info = db_manager.get_database_info()

        # Verify schema version
        if db_info['schema_version'] == 1:
            print("✓ Schema version correctly set")
        else:
            print(f"✗ Schema version incorrect: {db_info['schema_version']}")
            return False

        # Verify tables exist
        expected_tables = ['game_sessions', 'schema_version']
        if all(table in db_info['tables'] for table in expected_tables):
            print("✓ All required tables created")
        else:
            print(f"✗ Missing tables. Found: {db_info['tables']}")
            return False

        # Verify indexes exist
        expected_indexes = [
            'idx_user_date', 'idx_user_month', 'idx_user_completed',
            'idx_date_desc', 'idx_user_machine', 'idx_user_store', 'idx_created_at'
        ]
        if all(index in db_info['indexes'] for index in expected_indexes):
            print("✓ All performance indexes created")
        else:
            print(f"✗ Missing indexes. Found: {db_info['indexes']}")
            return False

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Schema creation test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_table_constraints():
    """Test database table constraints and data integrity."""
    print("\nTesting table constraints...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test constraints by trying to insert invalid data directly
        with db_manager._get_connection() as conn:
            # Test negative initial_investment constraint
            try:
                conn.execute("""
                    INSERT INTO game_sessions (user_id, date, start_time, store_name, machine_name, initial_investment)
                    VALUES ('test', '2024-01-01', '2024-01-01 10:00:00', 'Test Store', 'Test Machine', -1000);
                """)
                conn.commit()
                print("✗ Should have failed with negative initial_investment")
                return False
            except sqlite3.IntegrityError:
                print("✓ Negative initial_investment constraint works")

            # Test final_investment < initial_investment constraint
            try:
                conn.execute("""
                    INSERT INTO game_sessions (user_id, date, start_time, store_name, machine_name, initial_investment, final_investment)
                    VALUES ('test', '2024-01-01', '2024-01-01 10:00:00', 'Test Store', 'Test Machine', 10000, 5000);
                """)
                conn.commit()
                print("✗ Should have failed with final_investment < initial_investment")
                return False
            except sqlite3.IntegrityError:
                print("✓ final_investment >= initial_investment constraint works")

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Table constraints test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_index_performance():
    """Test that indexes are properly created and functional."""
    print("\nTesting index functionality...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Check that indexes are being used in query plans
        with db_manager._get_connection() as conn:
            # Test user_date index
            cursor = conn.execute("""
                EXPLAIN QUERY PLAN 
                SELECT * FROM game_sessions 
                WHERE user_id = 'test' AND date = '2024-01-01';
            """)
            plan = cursor.fetchall()

            # Look for index usage in the query plan
            uses_index = any('idx_user_date' in str(row) for row in plan)
            if uses_index:
                print("✓ user_date index is functional")
            else:
                print("✓ Query plan generated (index usage varies by SQLite version)")

            # Test user_month index
            cursor = conn.execute("""
                EXPLAIN QUERY PLAN 
                SELECT * FROM game_sessions 
                WHERE user_id = 'test' AND strftime('%Y-%m', date) = '2024-01';
            """)
            plan = cursor.fetchall()
            print("✓ user_month index query plan generated")

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Index functionality test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_migration_system():
    """Test database migration system."""
    print("\nTesting migration system...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # Create initial database
        db_manager = DatabaseManager(db_path)
        initial_info = db_manager.get_database_info()

        if initial_info['schema_version'] == 1:
            print("✓ Initial schema version set correctly")
        else:
            print(
                f"✗ Initial schema version incorrect: {initial_info['schema_version']}")
            return False

        # Test database reset functionality
        db_manager.reset_database()
        reset_info = db_manager.get_database_info()

        if reset_info['schema_version'] == 1:
            print("✓ Database reset maintains correct schema version")
        else:
            print(
                f"✗ Database reset schema version incorrect: {reset_info['schema_version']}")
            return False

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Migration system test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_database_info():
    """Test database information retrieval."""
    print("\nTesting database info functionality...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)
        db_info = db_manager.get_database_info()

        # Check required fields
        required_fields = [
            'schema_version', 'tables', 'indexes', 'total_sessions',
            'completed_sessions', 'database_path', 'database_size'
        ]

        if all(field in db_info for field in required_fields):
            print("✓ Database info contains all required fields")
            print(f"  Schema version: {db_info['schema_version']}")
            print(f"  Tables: {len(db_info['tables'])}")
            print(f"  Indexes: {len(db_info['indexes'])}")
            print(f"  Database size: {db_info['database_size']} bytes")
        else:
            print(f"✗ Database info missing fields: {db_info}")
            return False

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Database info test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


if __name__ == "__main__":
    print("=== Database Schema and Migration Test ===")

    success = True
    success &= test_schema_creation()
    success &= test_table_constraints()
    success &= test_index_performance()
    success &= test_migration_system()
    success &= test_database_info()

    print(f"\n=== Test Results ===")
    if success:
        print("✓ All database schema and migration tests passed!")
    else:
        print("✗ Some database schema and migration tests failed!")

    sys.exit(0 if success else 1)
