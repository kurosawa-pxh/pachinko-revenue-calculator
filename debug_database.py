#!/usr/bin/env python3
"""
Debug database connection issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def debug_database():
    with open('database_debug.txt', 'w', encoding='utf-8') as f:
        f.write("🔍 Database Connection Debug\n")
        f.write("=" * 50 + "\n\n")

        try:
            # Test imports
            f.write("1. Testing imports...\n")
            from src.config import get_config
            from src.database import DatabaseManager
            from src.models_fixed import GameSession
            from datetime import datetime, date
            f.write("✅ All imports successful\n\n")

            # Test config
            f.write("2. Testing config...\n")
            config = get_config()
            db_config = config.get_database_config()
            f.write(f"Database config: {db_config}\n\n")

            # Test database manager creation
            f.write("3. Testing DatabaseManager creation...\n")
            db_manager = DatabaseManager(config=config)
            f.write(f"✅ DatabaseManager created\n")
            f.write(f"Database type: {db_manager.db_type}\n")
            f.write(
                f"Database path: {getattr(db_manager, 'db_path', 'Not set')}\n\n")

            # Test database connection
            f.write("4. Testing database connection...\n")
            try:
                with db_manager._get_connection() as conn:
                    f.write("✅ Database connection successful\n")

                    # Test table existence
                    if db_manager.db_type == 'sqlite':
                        cursor = conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        f.write(
                            f"Tables found: {[table[0] for table in tables]}\n")

            except Exception as conn_error:
                f.write(f"❌ Database connection failed: {conn_error}\n")
                import traceback
                f.write(traceback.format_exc())
                f.write("\n")

            # Test session creation
            f.write("\n5. Testing session creation...\n")
            try:
                test_session = GameSession(
                    user_id="debug_user",
                    date=date.today(),
                    start_time=datetime.now(),
                    store_name="デバッグ店舗",
                    machine_name="デバッグ機種",
                    initial_investment=1000
                )
                f.write("✅ GameSession object created\n")

                # Try to save session
                session_id = db_manager.create_session(test_session)
                f.write(f"✅ Session saved with ID: {session_id}\n")

                # Try to retrieve session
                retrieved = db_manager.get_session(session_id)
                if retrieved:
                    f.write("✅ Session retrieved successfully\n")
                else:
                    f.write("❌ Failed to retrieve session\n")

                # Clean up
                db_manager.delete_session(session_id)
                f.write("✅ Test session cleaned up\n")

            except Exception as session_error:
                f.write(f"❌ Session operation failed: {session_error}\n")
                import traceback
                f.write(traceback.format_exc())
                f.write("\n")

            # Test database info
            f.write("\n6. Testing database info...\n")
            try:
                db_info = db_manager.get_database_info()
                f.write(f"Database info: {db_info}\n")
            except Exception as info_error:
                f.write(f"❌ Database info failed: {info_error}\n")
                import traceback
                f.write(traceback.format_exc())
                f.write("\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
            f.write("\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("Debug completed\n")


if __name__ == "__main__":
    debug_database()
    print("Database debug completed. Check database_debug.txt for results.")
