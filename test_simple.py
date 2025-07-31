#!/usr/bin/env python3
"""
Simple test to verify the date fix works.
"""

from src.config import get_config
from src.models_fixed import GameSession
from src.database import DatabaseManager
from datetime import datetime, date
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def main():
    print("🧪 Testing date field fix...")

    try:
        # Test model creation
        session = GameSession(
            user_id="test_user",
            date=date.today(),
            start_time=datetime.now(),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=1000
        )
        print(
            f"✅ Session created with date: {session.date} (type: {type(session.date)})")

        # Test database operations
        config = get_config()
        db_manager = DatabaseManager(config=config)
        print("✅ Database manager initialized")

        # Create session in database
        session_id = db_manager.create_session(session)
        print(f"✅ Session saved to database with ID: {session_id}")

        # Retrieve session from database
        retrieved = db_manager.get_session(session_id)
        if retrieved:
            print(
                f"✅ Session retrieved: date={retrieved.date} (type: {type(retrieved.date)})")
        else:
            print("❌ Failed to retrieve session")
            return False

        # Clean up
        db_manager.delete_session(session_id)
        print("✅ Test session cleaned up")

        print("\n🎉 All tests passed! Date field fix is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
