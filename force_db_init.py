#!/usr/bin/env python3
"""
Force database initialization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def force_db_init():
    with open('force_init_log.txt', 'w', encoding='utf-8') as f:
        f.write("🔧 Force Database Initialization\n")
        f.write("=" * 50 + "\n\n")

        try:
            from src.database import DatabaseManager
            from src.config import get_config

            f.write("1. Creating DatabaseManager...\n")
            config = get_config()
            db_manager = DatabaseManager(config=config)
            f.write("✅ DatabaseManager created\n")

            f.write("\n2. Checking initialization status...\n")
            is_initialized = db_manager._is_database_initialized()
            f.write(f"Database initialized: {is_initialized}\n")

            f.write("\n3. Force initialization...\n")
            try:
                with db_manager._get_connection() as conn:
                    f.write("✅ Connection obtained\n")

                    # Check current version
                    current_version = db_manager._get_schema_version(conn)
                    f.write(f"Current schema version: {current_version}\n")

                    if current_version == 0:
                        f.write("Initializing new database...\n")
                        db_manager._create_schema_version_table(conn)
                        db_manager._create_tables(conn)
                        db_manager._create_indexes(conn)
                        db_manager._set_schema_version(
                            conn, db_manager.CURRENT_SCHEMA_VERSION)
                        f.write("✅ Database initialized\n")
                    else:
                        f.write("Database already initialized\n")

                    # Test basic operations
                    f.write("\n4. Testing basic operations...\n")
                    cursor = conn.execute("SELECT COUNT(*) FROM game_sessions")
                    count = cursor.fetchone()[0]
                    f.write(f"Sessions count: {count}\n")

                    # Test table structure
                    cursor = conn.execute("PRAGMA table_info(game_sessions)")
                    columns = cursor.fetchall()
                    f.write(f"Table columns: {len(columns)}\n")
                    for col in columns:
                        f.write(f"  {col[1]} ({col[2]})\n")

            except Exception as conn_error:
                f.write(f"❌ Connection/initialization error: {conn_error}\n")
                f.write(f"Error type: {type(conn_error)}\n")
                f.write(f"Error args: {conn_error.args}\n")
                import traceback
                f.write(traceback.format_exc())

            f.write("\n5. Final verification...\n")
            try:
                # Test session creation
                from src.models_fixed import GameSession
                from datetime import datetime, date

                test_session = GameSession(
                    user_id="force_init_test",
                    date=date.today(),
                    start_time=datetime.now(),
                    store_name="テスト店舗",
                    machine_name="テスト機種",
                    initial_investment=1000
                )

                session_id = db_manager.create_session(test_session)
                f.write(f"✅ Test session created with ID: {session_id}\n")

                # Clean up
                db_manager.delete_session(session_id)
                f.write("✅ Test session cleaned up\n")

            except Exception as test_error:
                f.write(f"❌ Session test failed: {test_error}\n")
                f.write(f"Error type: {type(test_error)}\n")
                import traceback
                f.write(traceback.format_exc())

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        f.write("\n" + "=" * 50 + "\n")
        f.write("Force initialization completed\n")


if __name__ == "__main__":
    force_db_init()
    print("Force database initialization completed. Check force_init_log.txt for results.")
