#!/usr/bin/env python3
"""
Test session creation with detailed debugging
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_session_creation():
    with open('session_creation_test.txt', 'w', encoding='utf-8') as f:
        f.write("🧪 Session Creation Test\n")
        f.write("=" * 50 + "\n\n")

        try:
            from src.database import DatabaseManager
            from src.config import get_config
            from src.models_fixed import GameSession
            from datetime import datetime, date

            f.write("1. Setting up test environment...\n")
            config = get_config()
            db_manager = DatabaseManager(config=config)
            f.write(
                f"✅ DatabaseManager created with db_type: {db_manager.db_type}\n")

            f.write("\n2. Creating test session...\n")
            test_session = GameSession(
                user_id="test_session_creation",
                date=date.today(),
                start_time=datetime.now(),
                store_name="テスト店舗",
                machine_name="テスト機種",
                initial_investment=1000
            )
            f.write("✅ GameSession object created\n")

            f.write("\n3. Attempting to save session...\n")
            try:
                session_id = db_manager.create_session(test_session)
                f.write(
                    f"✅ Session created successfully with ID: {session_id}\n")

                # Verify the session was saved
                retrieved = db_manager.get_session(session_id)
                if retrieved:
                    f.write("✅ Session retrieved successfully\n")
                    f.write(f"Retrieved session: {retrieved}\n")
                else:
                    f.write("❌ Failed to retrieve saved session\n")

                # Clean up
                db_manager.delete_session(session_id)
                f.write("✅ Test session cleaned up\n")

            except Exception as create_error:
                f.write(f"❌ Session creation failed: {create_error}\n")
                f.write(f"Error type: {type(create_error)}\n")
                f.write(f"Error args: {create_error.args}\n")
                import traceback
                f.write(traceback.format_exc())
                f.write("\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        f.write("\n" + "=" * 50 + "\n")
        f.write("Session creation test completed\n")


if __name__ == "__main__":
    test_session_creation()
    print("Session creation test completed. Check session_creation_test.txt for results.")
