#!/usr/bin/env python3
"""
Debug the specific connection error with value 0
"""

import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def debug_connection_error():
    with open('connection_error_debug.txt', 'w', encoding='utf-8') as f:
        f.write("🔍 Connection Error Debug (Error: 0)\n")
        f.write("=" * 50 + "\n\n")

        try:
            # Test direct SQLite connection
            f.write("1. Testing direct SQLite connection...\n")
            try:
                conn = sqlite3.connect('pachinko_data.db')
                f.write("✅ Direct SQLite connection successful\n")

                # Test basic query
                cursor = conn.execute("SELECT COUNT(*) FROM game_sessions")
                count = cursor.fetchone()[0]
                f.write(f"✅ Query successful, sessions count: {count}\n")
                conn.close()

            except Exception as sqlite_error:
                f.write(f"❌ Direct SQLite connection failed: {sqlite_error}\n")
                f.write(f"Error type: {type(sqlite_error)}\n")
                f.write(f"Error args: {sqlite_error.args}\n")

            f.write("\n2. Testing DatabaseManager connection...\n")
            try:
                from src.database import DatabaseManager
                from src.config import get_config

                config = get_config()
                db_manager = DatabaseManager(config=config)
                f.write("✅ DatabaseManager created\n")

                # Test connection context manager
                try:
                    with db_manager._get_connection() as conn:
                        f.write("✅ DatabaseManager connection successful\n")
                        cursor = conn.execute(
                            "SELECT COUNT(*) FROM game_sessions")
                        count = cursor.fetchone()[0]
                        f.write(
                            f"✅ DatabaseManager query successful, count: {count}\n")

                except Exception as conn_error:
                    f.write(
                        f"❌ DatabaseManager connection failed: {conn_error}\n")
                    f.write(f"Error type: {type(conn_error)}\n")
                    f.write(f"Error args: {conn_error.args}\n")
                    f.write(f"Error repr: {repr(conn_error)}\n")

                    # Check if it's the mysterious "0" error
                    if str(conn_error) == "0":
                        f.write("🚨 Found the mysterious '0' error!\n")
                        f.write(
                            "This suggests an exception with numeric value 0\n")

            except Exception as db_error:
                f.write(f"❌ DatabaseManager creation failed: {db_error}\n")
                import traceback
                f.write(traceback.format_exc())

            f.write("\n3. Testing config values...\n")
            try:
                from src.config import get_config
                config = get_config()
                db_config = config.get_database_config()
                f.write(f"Database config: {db_config}\n")

                # Check file permissions
                db_path = db_config.get('path', 'pachinko_data.db')
                if os.path.exists(db_path):
                    stat = os.stat(db_path)
                    f.write(f"Database file exists: {db_path}\n")
                    f.write(f"File size: {stat.st_size} bytes\n")
                    f.write(f"File permissions: {oct(stat.st_mode)}\n")
                else:
                    f.write(f"❌ Database file missing: {db_path}\n")

            except Exception as config_error:
                f.write(f"❌ Config test failed: {config_error}\n")

            f.write("\n4. Testing with minimal example...\n")
            try:
                # Minimal test that mimics the actual usage
                import sqlite3
                from contextlib import contextmanager

                @contextmanager
                def test_connection():
                    conn = None
                    try:
                        conn = sqlite3.connect('pachinko_data.db')
                        conn.row_factory = sqlite3.Row
                        yield conn
                    except Exception as e:
                        if conn:
                            conn.rollback()
                        f.write(f"Connection error in context manager: {e}\n")
                        f.write(f"Error type: {type(e)}\n")
                        f.write(f"Error repr: {repr(e)}\n")
                        raise e
                    finally:
                        if conn:
                            conn.close()

                with test_connection() as conn:
                    f.write("✅ Minimal context manager test successful\n")

            except Exception as minimal_error:
                f.write(f"❌ Minimal test failed: {minimal_error}\n")
                f.write(f"Error type: {type(minimal_error)}\n")
                f.write(f"Error repr: {repr(minimal_error)}\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        f.write("\n" + "=" * 50 + "\n")
        f.write("Connection error debug completed\n")


if __name__ == "__main__":
    debug_connection_error()
    print("Connection error debug completed. Check connection_error_debug.txt for results.")
