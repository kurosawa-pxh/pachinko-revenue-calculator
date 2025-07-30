#!/usr/bin/env python3
"""
Test script to verify the DatabaseManager implementation.
"""

from src.models_fixed import GameSession, ValidationError
from src.database import DatabaseManager, DatabaseError
import sys
import os
import tempfile
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_database_initialization():
    """Test database initialization and table creation."""
    print("Testing database initialization...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database
        db_manager = DatabaseManager(db_path)
        print("✓ Database initialized successfully")

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_session_crud_operations():
    """Test CRUD operations for game sessions."""
    print("\nTesting CRUD operations...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create a test session
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )

        # Test CREATE
        session_id = db_manager.create_session(session)
        print(f"✓ Session created with ID: {session_id}")

        # Test READ
        retrieved_session = db_manager.get_session(session_id)
        if retrieved_session and retrieved_session.user_id == "test_user":
            print("✓ Session retrieved successfully")
        else:
            print("✗ Failed to retrieve session")
            return False

        # Complete the session
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )

        # Test UPDATE
        if db_manager.update_session(session_id, session):
            print("✓ Session updated successfully")
        else:
            print("✗ Failed to update session")
            return False

        # Test READ after update
        updated_session = db_manager.get_session(session_id)
        if updated_session and updated_session.is_completed and updated_session.profit == 5000:
            print("✓ Updated session retrieved with correct profit")
        else:
            print("✗ Updated session data incorrect")
            return False

        # Test get_sessions
        sessions = db_manager.get_sessions("test_user")
        if len(sessions) == 1 and sessions[0].id == session_id:
            print("✓ get_sessions works correctly")
        else:
            print("✗ get_sessions failed")
            return False

        # Test DELETE
        if db_manager.delete_session(session_id):
            print("✓ Session deleted successfully")
        else:
            print("✗ Failed to delete session")
            return False

        # Verify deletion
        deleted_session = db_manager.get_session(session_id)
        if deleted_session is None:
            print("✓ Session deletion verified")
        else:
            print("✗ Session not properly deleted")
            return False

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ CRUD operations failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_error_handling():
    """Test error handling and transaction management."""
    print("\nTesting error handling...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test validation error handling
        try:
            invalid_session = GameSession(
                user_id="",  # Invalid empty user_id
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            db_manager.create_session(invalid_session)
            print("✗ Should have failed with validation error")
            return False
        except ValidationError:
            print("✓ Validation error properly handled")

        # Test non-existent session operations
        try:
            db_manager.get_session(99999)  # Non-existent ID
            print("✓ Non-existent session handled gracefully")
        except DatabaseError:
            print("✗ Should handle non-existent session gracefully")
            return False

        # Test update non-existent session
        try:
            valid_session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            db_manager.update_session(99999, valid_session)
            print("✗ Should have failed with non-existent session")
            return False
        except DatabaseError:
            print("✓ Non-existent session update error properly handled")

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_monthly_stats():
    """Test monthly statistics functionality."""
    print("\nTesting monthly statistics...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create multiple test sessions
        sessions = []
        for i in range(3):
            session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15 + i),
                start_time=datetime(2024, 1, 15 + i, 10, 0),
                store_name=f"テストホール{i+1}",
                machine_name="CR花の慶次",
                initial_investment=10000
            )

            # Complete sessions with different profits
            session.complete_session(
                end_time=datetime(2024, 1, 15 + i, 12, 0),
                final_investment=15000,
                return_amount=20000 - (i * 5000)  # Decreasing returns
            )

            session_id = db_manager.create_session(session)
            sessions.append((session_id, session))

        # Get monthly stats
        stats = db_manager.get_monthly_stats("test_user", 2024, 1)

        if stats['total_sessions'] == 3 and stats['completed_sessions'] == 3:
            print("✓ Monthly stats calculated correctly")
            print(f"  Total sessions: {stats['total_sessions']}")
            print(f"  Total profit: {stats['total_profit']}")
            print(f"  Win rate: {stats['win_rate']:.1f}%")
        else:
            print("✗ Monthly stats calculation failed")
            return False

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Monthly stats test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_data_integrity():
    """Test data integrity checking functionality."""
    print("\nTesting data integrity...")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create a valid session
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )

        db_manager.create_session(session)

        # Check data integrity
        integrity_result = db_manager.check_data_integrity()

        if integrity_result['total_records'] == 1 and not integrity_result['has_issues']:
            print("✓ Data integrity check passed")
        else:
            print("✗ Data integrity check failed")
            return False

        # Clean up
        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Data integrity test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


if __name__ == "__main__":
    print("=== DatabaseManager Test ===")

    success = True
    success &= test_database_initialization()
    success &= test_session_crud_operations()
    success &= test_error_handling()
    success &= test_monthly_stats()
    success &= test_data_integrity()

    print(f"\n=== Test Results ===")
    if success:
        print("✓ All DatabaseManager tests passed!")
    else:
        print("✗ Some DatabaseManager tests failed!")

    sys.exit(0 if success else 1)
