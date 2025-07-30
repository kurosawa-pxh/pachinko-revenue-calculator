#!/usr/bin/env python3
"""
Simple test script to verify the GameSession model implementation.
"""

from src.models_fixed import GameSession, ValidationError
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def test_game_session_creation():
    """Test basic GameSession creation and validation."""
    print("Testing GameSession creation...")

    # Test valid session creation
    try:
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        print("✓ Valid session created successfully")
        print(f"  Session: {session}")
    except Exception as e:
        print(f"✗ Failed to create valid session: {e}")
        return False

    # Test validation errors
    print("\nTesting validation errors...")

    # Test empty user_id
    try:
        GameSession(
            user_id="",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        print("✗ Should have failed with empty user_id")
        return False
    except ValidationError as e:
        print(f"✓ Correctly caught validation error: {e}")

    # Test negative investment
    try:
        GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=-1000
        )
        print("✗ Should have failed with negative investment")
        return False
    except ValidationError as e:
        print(f"✓ Correctly caught validation error: {e}")

    return True


def test_session_completion():
    """Test session completion functionality."""
    print("\nTesting session completion...")

    # Create initial session
    session = GameSession(
        user_id="test_user",
        date=datetime(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 10, 0),
        store_name="テストホール",
        machine_name="CR花の慶次",
        initial_investment=10000
    )

    # Complete the session
    try:
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )
        print("✓ Session completed successfully")
        print(f"  Profit: {session.profit}")
        print(f"  Status: {'完了' if session.is_completed else '進行中'}")
    except Exception as e:
        print(f"✗ Failed to complete session: {e}")
        return False

    # Test invalid completion (end time before start time)
    try:
        session2 = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        session2.complete_session(
            end_time=datetime(2024, 1, 15, 9, 0),  # Before start time
            final_investment=15000,
            return_amount=20000
        )
        print("✗ Should have failed with invalid end time")
        return False
    except ValidationError as e:
        print(f"✓ Correctly caught validation error: {e}")

    return True


def test_dict_conversion():
    """Test dictionary conversion methods."""
    print("\nTesting dictionary conversion...")

    # Create and complete a session
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

    # Convert to dict
    session_dict = session.to_dict()
    print("✓ Converted to dictionary")

    # Convert back from dict
    try:
        session2 = GameSession.from_dict(session_dict)
        print("✓ Converted back from dictionary")
        print(f"  Original profit: {session.profit}")
        print(f"  Restored profit: {session2.profit}")

        if session.profit == session2.profit and session.user_id == session2.user_id:
            print("✓ Data integrity maintained")
        else:
            print("✗ Data integrity lost")
            return False
    except Exception as e:
        print(f"✗ Failed to convert from dictionary: {e}")
        return False

    return True


if __name__ == "__main__":
    print("=== GameSession Model Test ===")

    success = True
    success &= test_game_session_creation()
    success &= test_session_completion()
    success &= test_dict_conversion()

    print(f"\n=== Test Results ===")
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")

    sys.exit(0 if success else 1)
