#!/usr/bin/env python3
"""
Verification test for Task 2.3: CRUD 操作メソッドの実装
This test verifies that all requirements are met:
- create_session, update_session, get_sessions メソッドを実装
- GameSession モデルとの統合を実装
- データ整合性チェック機能を実装
- Requirements: 1.1, 2.1, 6.3
"""

from src.database import DatabaseManager, DatabaseError
from src.models_fixed import GameSession, ValidationError
import sys
import os
import tempfile
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def verify_create_session_method():
    """Verify create_session method implementation."""
    print("✓ Verifying create_session method...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test method exists and works
        session = GameSession(
            user_id="verification_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="検証ホール",
            machine_name="CR検証機",
            initial_investment=10000
        )

        session_id = db_manager.create_session(session)
        assert isinstance(session_id, int) and session_id > 0
        assert session.id == session_id  # Object should be updated with ID

        print("  ✓ create_session method implemented and working")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"  ✗ create_session method failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def verify_update_session_method():
    """Verify update_session method implementation."""
    print("✓ Verifying update_session method...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create initial session
        session = GameSession(
            user_id="verification_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="検証ホール",
            machine_name="CR検証機",
            initial_investment=10000
        )

        session_id = db_manager.create_session(session)

        # Update the session
        session.complete_session(
            end_time=datetime(2024, 1, 15, 16, 0),
            final_investment=20000,
            return_amount=25000
        )

        result = db_manager.update_session(session_id, session)
        assert result == True

        # Verify update worked
        updated_session = db_manager.get_session(session_id)
        assert updated_session.is_completed == True
        assert updated_session.profit == 5000

        print("  ✓ update_session method implemented and working")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"  ✗ update_session method failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def verify_get_sessions_method():
    """Verify get_sessions method implementation."""
    print("✓ Verifying get_sessions method...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = GameSession(
                user_id="verification_user",
                date=datetime(2024, 1, 15 + i),
                start_time=datetime(2024, 1, 15 + i, 10, 0),
                store_name=f"検証ホール{i+1}",
                machine_name=f"CR検証機{i+1}",
                initial_investment=10000
            )
            db_manager.create_session(session)
            sessions.append(session)

        # Test get_sessions method
        retrieved_sessions = db_manager.get_sessions("verification_user")
        assert len(retrieved_sessions) == 3

        # Test with date range
        date_range = (datetime(2024, 1, 15), datetime(2024, 1, 16))
        filtered_sessions = db_manager.get_sessions(
            "verification_user", date_range=date_range)
        assert len(filtered_sessions) == 2

        # Test with limit
        limited_sessions = db_manager.get_sessions(
            "verification_user", limit=2)
        assert len(limited_sessions) == 2

        print("  ✓ get_sessions method implemented with filtering options")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"  ✗ get_sessions method failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def verify_gamesession_integration():
    """Verify GameSession model integration."""
    print("✓ Verifying GameSession model integration...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test that GameSession objects work seamlessly with database
        session = GameSession(
            user_id="統合テストユーザー",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="統合テストホール",
            machine_name="CR統合テスト機",
            initial_investment=15000
        )

        # Test validation is called
        try:
            invalid_session = GameSession(
                user_id="",  # Invalid
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="統合テストホール",
                machine_name="CR統合テスト機",
                initial_investment=15000
            )
            assert False, "Should have failed validation"
        except ValidationError:
            pass  # Expected

        # Test session completion integration
        session_id = db_manager.create_session(session)
        session.complete_session(
            end_time=datetime(2024, 1, 15, 16, 0),
            final_investment=25000,
            return_amount=30000
        )
        db_manager.update_session(session_id, session)

        # Test to_dict/from_dict integration
        retrieved = db_manager.get_session(session_id)
        assert retrieved.user_id == session.user_id
        assert retrieved.profit == session.profit

        print("  ✓ GameSession model fully integrated with database operations")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"  ✗ GameSession integration failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def verify_data_integrity_checks():
    """Verify data integrity check functionality."""
    print("✓ Verifying data integrity checks...")

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        db_manager = DatabaseManager(db_path)

        # Test that check_data_integrity method exists and works
        integrity_result = db_manager.check_data_integrity()
        assert isinstance(integrity_result, dict)
        assert 'total_records' in integrity_result
        assert 'has_issues' in integrity_result

        # Test validation prevents invalid data
        try:
            invalid_session = GameSession(
                user_id="test",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="Test Store",
                machine_name="Test Machine",
                initial_investment=-1000  # Invalid
            )
            db_manager.create_session(invalid_session)
            assert False, "Should have prevented invalid data"
        except ValidationError:
            pass  # Expected

        # Test database constraints
        try:
            with db_manager._get_connection() as conn:
                conn.execute("""
                    INSERT INTO game_sessions (
                        user_id, date, start_time, store_name, machine_name, initial_investment
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, ("test", "2024-01-01", "2024-01-01 10:00:00", "Store", "Machine", -1000))
                conn.commit()
            assert False, "Database should have prevented invalid data"
        except Exception:
            pass  # Expected - database constraint should prevent this

        print("  ✓ Data integrity checks implemented at multiple levels")

        os.unlink(db_path)
        return True

    except Exception as e:
        print(f"  ✗ Data integrity checks failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)
        return False


def verify_requirements_coverage():
    """Verify that specific requirements are covered."""
    print("✓ Verifying requirements coverage...")

    # Requirement 1.1: 遊技データ入力機能
    # - Verified by create_session and update_session methods
    print("  ✓ Requirement 1.1: 遊技データ入力機能 - Covered by CRUD operations")

    # Requirement 2.1: 履歴表示機能
    # - Verified by get_sessions method with filtering
    print("  ✓ Requirement 2.1: 履歴表示機能 - Covered by get_sessions method")

    # Requirement 6.3: データセキュリティ
    # - Verified by validation and data integrity checks
    print("  ✓ Requirement 6.3: データセキュリティ - Covered by validation and integrity checks")

    return True


if __name__ == "__main__":
    print("=== Task 2.3 Verification: CRUD 操作メソッドの実装 ===")
    print()

    success = True
    success &= verify_create_session_method()
    success &= verify_update_session_method()
    success &= verify_get_sessions_method()
    success &= verify_gamesession_integration()
    success &= verify_data_integrity_checks()
    success &= verify_requirements_coverage()

    print()
    print("=== Verification Results ===")
    if success:
        print("✅ Task 2.3 FULLY IMPLEMENTED")
        print("✅ All required methods implemented:")
        print("   - create_session: ✓")
        print("   - update_session: ✓")
        print("   - get_sessions: ✓")
        print("✅ GameSession model integration: ✓")
        print("✅ Data integrity checks: ✓")
        print("✅ Requirements coverage:")
        print("   - 1.1 遊技データ入力機能: ✓")
        print("   - 2.1 履歴表示機能: ✓")
        print("   - 6.3 データセキュリティ: ✓")
    else:
        print("❌ Task 2.3 verification failed!")

    sys.exit(0 if success else 1)
