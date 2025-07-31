#!/usr/bin/env python3
"""
Test script to verify the date field fix in the database.
"""

from src.config import get_config
from src.models_fixed import GameSession
from src.database import DatabaseManager
from datetime import datetime, date
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_date_fix():
    """Test that the date field works correctly."""
    print("Testing date field fix...")

    try:
        # Initialize database manager
        config = get_config()
        db_manager = DatabaseManager(config=config)

        # Create a test session with date field
        test_session = GameSession(
            user_id="test_user",
            date=date.today(),  # This should be a date object, not datetime
            start_time=datetime.now(),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=1000
        )

        print(
            f"Created session with date: {test_session.date} (type: {type(test_session.date)})")

        # Try to save the session
        session_id = db_manager.create_session(test_session)
        print(f"Successfully created session with ID: {session_id}")

        # Try to retrieve the session
        retrieved_session = db_manager.get_session(session_id)
        if retrieved_session:
            print(
                f"Retrieved session date: {retrieved_session.date} (type: {type(retrieved_session.date)})")
            print("✅ Date field fix successful!")
        else:
            print("❌ Failed to retrieve session")

        # Clean up
        db_manager.delete_session(session_id)
        print("Test session cleaned up")

    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_date_fix()
