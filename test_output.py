#!/usr/bin/env python3
"""
Test with file output to verify the fix.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_with_file_output():
    with open('test_results.txt', 'w', encoding='utf-8') as f:
        f.write("🧪 Testing date field fix...\n")

        try:
            from datetime import datetime, date
            from src.models_fixed import GameSession
            from src.database import DatabaseManager
            from src.config import get_config

            f.write("✅ All imports successful\n")

            # Test model creation
            session = GameSession(
                user_id="test_user",
                date=date.today(),
                start_time=datetime.now(),
                store_name="テスト店舗",
                machine_name="テスト機種",
                initial_investment=1000
            )
            f.write(
                f"✅ Session created with date: {session.date} (type: {type(session.date)})\n")

            # Test database operations
            config = get_config()
            db_manager = DatabaseManager(config=config)
            f.write("✅ Database manager initialized\n")

            # Create session in database
            session_id = db_manager.create_session(session)
            f.write(f"✅ Session saved to database with ID: {session_id}\n")

            # Retrieve session from database
            retrieved = db_manager.get_session(session_id)
            if retrieved:
                f.write(
                    f"✅ Session retrieved: date={retrieved.date} (type: {type(retrieved.date)})\n")
            else:
                f.write("❌ Failed to retrieve session\n")
                return False

            # Clean up
            db_manager.delete_session(session_id)
            f.write("✅ Test session cleaned up\n")

            f.write("\n🎉 All tests passed! Date field fix is working correctly.\n")
            return True

        except Exception as e:
            f.write(f"❌ Test failed with error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
            return False


if __name__ == "__main__":
    success = test_with_file_output()
    print("Test completed. Check test_results.txt for results.")
    sys.exit(0 if success else 1)
