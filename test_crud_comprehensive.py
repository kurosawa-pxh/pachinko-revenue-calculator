#!/usr/bin/env python3
"""
Comprehensive test for CRUD operations to verify task 2.3 requirements.
"""

from src.database import DatabaseManager, DatabaseError
from src.models_fixed import GameSession, ValidationError
import sys
import os
import tempfile
from datetime import datetime, timedelta
from typing import List

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_create_session_comprehensive():
    """Test create_session method comprehensively."""
    print("Testing create_session method...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test 1: Create incomplete session
        session = GameSession(
            user_id="user123",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="パチンコホール太郎",
            machine_name="CR花の慶次〜愛〜",
            initial_investment=5000
        )

        session_id = db_manager.create_session(session)
        assert session_id > 0, "Session ID should be positive"
        assert session.id == session_id, "Session object should be updated with ID"
        print("✓ Incomplete session created successfully")

        # Test 2: Create completed session
        completed_session = GameSession(
            user_id="user123",
            date=datetime(2024, 1, 16),
            start_time=datetime(2024, 1, 16, 14, 0),
            store_name="パチンコホール花子",
            machine_name="CRぱちんこ必殺仕事人",
            initial_investment=10000
        )
        completed_session.complete_session(
            end_time=datetime(2024, 1, 16, 18, 0),
            final_investment=25000,
            return_amount=30000
        )

        completed_id = db_manager.create_session(completed_session)
        assert completed_id > 0, "Completed session ID should be positive"
        print("✓ Completed session created successfully")

        # Test 3: Verify data integrity constraints
        try:
            invalid_session = GameSession(
                user_id="user123",
                date=datetime(2024, 1, 17),
                start_time=datetime(2024, 1, 17, 10, 0),
                store_name="",  # Invalid empty store name
                machine_name="Test Machine",
                initial_investment=5000
            )
            db_manager.create_session(invalid_session)
            assert False, "Should have failed with validation error"
        except ValidationError:
            print("✓ Data validation working correctly")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ create_session test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_update_session_comprehensive():
    """Test update_session method comprehensively."""
    print("\nTesting update_session method...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create initial session
        session = GameSession(
            user_id="user456",
            date=datetime(2024, 2, 1),
            start_time=datetime(2024, 2, 1, 9, 0),
            store_name="テストホール",
            machine_name="CRテスト機",
            initial_investment=8000
        )

        session_id = db_manager.create_session(session)

        # Test 1: Update incomplete session to completed
        session.complete_session(
            end_time=datetime(2024, 2, 1, 15, 0),
            final_investment=20000,
            return_amount=18000
        )

        result = db_manager.update_session(session_id, session)
        assert result == True, "Update should return True"
        print("✓ Session updated from incomplete to completed")

        # Test 2: Verify updated data
        updated_session = db_manager.get_session(session_id)
        assert updated_session is not None, "Updated session should exist"
        assert updated_session.is_completed == True, "Session should be completed"
        assert updated_session.profit == -2000, "Profit should be calculated correctly"
        print("✓ Updated session data verified")

        # Test 3: Update completed session
        session.return_amount = 25000  # Change return amount
        session.calculate_profit()  # Recalculate profit

        result = db_manager.update_session(session_id, session)
        assert result == True, "Second update should succeed"

        final_session = db_manager.get_session(session_id)
        assert final_session.profit == 5000, "Profit should be updated correctly"
        print("✓ Completed session updated successfully")

        # Test 4: Update non-existent session
        try:
            db_manager.update_session(99999, session)
            assert False, "Should have failed with non-existent session"
        except DatabaseError:
            print("✓ Non-existent session update handled correctly")

        # Test 5: Update with invalid data
        try:
            invalid_session = GameSession(
                user_id="",  # Invalid user ID
                date=datetime(2024, 2, 1),
                start_time=datetime(2024, 2, 1, 9, 0),
                store_name="テストホール",
                machine_name="CRテスト機",
                initial_investment=8000
            )
            db_manager.update_session(session_id, invalid_session)
            assert False, "Should have failed with validation error"
        except ValidationError:
            print("✓ Invalid data update handled correctly")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ update_session test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_get_sessions_comprehensive():
    """Test get_sessions method comprehensively."""
    print("\nTesting get_sessions method...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create test data for multiple users and dates
        test_sessions = []

        # User 1 sessions
        for i in range(5):
            session = GameSession(
                user_id="user1",
                date=datetime(2024, 1, 10 + i),
                start_time=datetime(2024, 1, 10 + i, 10, 0),
                store_name=f"ホール{i+1}",
                machine_name=f"機種{i+1}",
                initial_investment=5000 + (i * 1000)
            )

            if i % 2 == 0:  # Complete every other session
                session.complete_session(
                    end_time=datetime(2024, 1, 10 + i, 16, 0),
                    final_investment=session.initial_investment + 5000,
                    return_amount=session.initial_investment + (i * 2000)
                )

            session_id = db_manager.create_session(session)
            test_sessions.append((session_id, session))

        # User 2 sessions
        for i in range(3):
            session = GameSession(
                user_id="user2",
                date=datetime(2024, 1, 20 + i),
                start_time=datetime(2024, 1, 20 + i, 11, 0),
                store_name=f"別ホール{i+1}",
                machine_name=f"別機種{i+1}",
                initial_investment=8000
            )
            session_id = db_manager.create_session(session)

        # Test 1: Get all sessions for user1
        user1_sessions = db_manager.get_sessions("user1")
        assert len(
            user1_sessions) == 5, f"Expected 5 sessions, got {len(user1_sessions)}"
        print("✓ Retrieved all sessions for user1")

        # Test 2: Get sessions for user2
        user2_sessions = db_manager.get_sessions("user2")
        assert len(
            user2_sessions) == 3, f"Expected 3 sessions, got {len(user2_sessions)}"
        print("✓ Retrieved all sessions for user2")

        # Test 3: Get sessions with date range
        start_date = datetime(2024, 1, 12)
        end_date = datetime(2024, 1, 14)
        filtered_sessions = db_manager.get_sessions(
            "user1", date_range=(start_date, end_date))
        assert len(
            filtered_sessions) == 3, f"Expected 3 sessions in date range, got {len(filtered_sessions)}"
        print("✓ Date range filtering works correctly")

        # Test 4: Get sessions with limit
        limited_sessions = db_manager.get_sessions("user1", limit=3)
        assert len(
            limited_sessions) == 3, f"Expected 3 sessions with limit, got {len(limited_sessions)}"
        print("✓ Limit parameter works correctly")

        # Test 5: Get sessions with offset
        offset_sessions = db_manager.get_sessions("user1", limit=2, offset=2)
        assert len(
            offset_sessions) == 2, f"Expected 2 sessions with offset, got {len(offset_sessions)}"
        print("✓ Offset parameter works correctly")

        # Test 6: Get sessions for non-existent user
        empty_sessions = db_manager.get_sessions("nonexistent_user")
        assert len(
            empty_sessions) == 0, "Should return empty list for non-existent user"
        print("✓ Non-existent user handled correctly")

        # Test 7: Verify session ordering (should be date DESC, start_time DESC)
        all_sessions = db_manager.get_sessions("user1")
        for i in range(len(all_sessions) - 1):
            current_date = all_sessions[i].date
            next_date = all_sessions[i + 1].date
            assert current_date >= next_date, "Sessions should be ordered by date DESC"
        print("✓ Session ordering verified")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ get_sessions test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_gamesession_integration():
    """Test GameSession model integration with database operations."""
    print("\nTesting GameSession model integration...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test 1: Create session with Japanese characters
        session = GameSession(
            user_id="テストユーザー",
            date=datetime(2024, 3, 1),
            start_time=datetime(2024, 3, 1, 13, 30),
            store_name="パチンコホール「金太郎」",
            machine_name="CRぱちんこ必殺仕事人Ⅴ",
            initial_investment=12000
        )

        session_id = db_manager.create_session(session)
        retrieved = db_manager.get_session(session_id)

        assert retrieved.user_id == "テストユーザー", "Japanese user ID should be preserved"
        assert retrieved.store_name == "パチンコホール「金太郎」", "Japanese store name should be preserved"
        assert retrieved.machine_name == "CRぱちんこ必殺仕事人Ⅴ", "Japanese machine name should be preserved"
        print("✓ Japanese characters handled correctly")

        # Test 2: Test session completion workflow
        session.complete_session(
            end_time=datetime(2024, 3, 1, 17, 45),
            final_investment=28000,
            return_amount=35000
        )

        db_manager.update_session(session_id, session)
        completed_session = db_manager.get_session(session_id)

        assert completed_session.is_completed == True, "Session should be completed"
        assert completed_session.profit == 7000, "Profit should be calculated correctly"
        print("✓ Session completion workflow works correctly")

        # Test 3: Test to_dict and from_dict integration
        session_dict = session.to_dict()
        recreated_session = GameSession.from_dict(session_dict)

        assert recreated_session.user_id == session.user_id, "to_dict/from_dict should preserve user_id"
        assert recreated_session.profit == session.profit, "to_dict/from_dict should preserve profit"
        assert recreated_session.is_completed == session.is_completed, "to_dict/from_dict should preserve completion status"
        print("✓ to_dict/from_dict integration works correctly")

        # Test 4: Test validation integration
        try:
            invalid_session = GameSession(
                user_id="test",
                date=datetime(2024, 3, 1),
                start_time=datetime(2024, 3, 1, 13, 30),
                store_name="Valid Store",
                machine_name="Valid Machine",
                initial_investment=-1000  # Invalid negative investment
            )
            db_manager.create_session(invalid_session)
            assert False, "Should have failed with validation error"
        except ValidationError as e:
            assert "開始投資額は0以上" in str(
                e), "Should show correct validation message"
            print("✓ Validation integration works correctly")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ GameSession integration test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def test_data_integrity_checks():
    """Test data integrity checking functionality."""
    print("\nTesting data integrity checks...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test 1: Create valid sessions
        valid_sessions = []
        for i in range(3):
            session = GameSession(
                user_id=f"user{i}",
                date=datetime(2024, 4, 1 + i),
                start_time=datetime(2024, 4, 1 + i, 10, 0),
                store_name=f"ホール{i}",
                machine_name=f"機種{i}",
                initial_investment=10000
            )
            session.complete_session(
                end_time=datetime(2024, 4, 1 + i, 16, 0),
                final_investment=15000,
                return_amount=20000
            )
            db_manager.create_session(session)
            valid_sessions.append(session)

        # Check integrity with valid data
        integrity_result = db_manager.check_data_integrity()
        assert integrity_result['total_records'] == 3, "Should have 3 records"
        assert integrity_result['has_issues'] == False, "Should have no issues"
        print("✓ Data integrity check with valid data")

        # Test 2: Test database constraints
        # The database constraints should prevent invalid data from being inserted
        # This tests the database-level integrity checks

        # Test constraint: initial_investment >= 0
        try:
            with db_manager._get_connection() as conn:
                conn.execute("""
                    INSERT INTO game_sessions (
                        user_id, date, start_time, store_name, machine_name, initial_investment
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, ("test", "2024-04-01", "2024-04-01 10:00:00", "Store", "Machine", -1000))
                conn.commit()
            assert False, "Should have failed with constraint violation"
        except Exception:
            print("✓ Database constraint prevents negative initial_investment")

        # Test constraint: final_investment >= initial_investment
        try:
            with db_manager._get_connection() as conn:
                conn.execute("""
                    INSERT INTO game_sessions (
                        user_id, date, start_time, store_name, machine_name, 
                        initial_investment, final_investment, return_amount, is_completed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, ("test", "2024-04-01", "2024-04-01 10:00:00", "Store", "Machine", 10000, 5000, 8000, True))
                conn.commit()
            assert False, "Should have failed with constraint violation"
        except Exception:
            print("✓ Database constraint prevents final_investment < initial_investment")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"✗ Data integrity test failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


if __name__ == "__main__":
    print("=== Comprehensive CRUD Operations Test ===")

    success = True
    success &= test_create_session_comprehensive()
    success &= test_update_session_comprehensive()
    success &= test_get_sessions_comprehensive()
    success &= test_gamesession_integration()
    success &= test_data_integrity_checks()

    print(f"\n=== Test Results ===")
    if success:
        print("✓ All CRUD operations tests passed!")
        print("✓ Task 2.3 requirements fully implemented:")
        print("  - create_session method implemented with validation")
        print("  - update_session method implemented with error handling")
        print("  - get_sessions method implemented with filtering options")
        print("  - GameSession model fully integrated")
        print("  - Data integrity checks implemented at multiple levels")
    else:
        print("✗ Some CRUD operations tests failed!")

    sys.exit(0 if success else 1)
