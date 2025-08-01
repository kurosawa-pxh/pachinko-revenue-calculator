#!/usr/bin/env python3
"""
Test SQLite connection directly
"""

import sqlite3
import os


def test_sqlite():
    with open('sqlite_test.txt', 'w', encoding='utf-8') as f:
        f.write("🔍 SQLite Direct Test\n")
        f.write("=" * 50 + "\n\n")

        try:
            # Test file existence and permissions
            db_path = 'pachinko_data.db'
            f.write(f"1. Checking database file: {db_path}\n")

            if os.path.exists(db_path):
                stat = os.stat(db_path)
                f.write(f"✅ File exists, size: {stat.st_size} bytes\n")
                f.write(f"Permissions: {oct(stat.st_mode)}\n")
                f.write(f"Readable: {os.access(db_path, os.R_OK)}\n")
                f.write(f"Writable: {os.access(db_path, os.W_OK)}\n")
            else:
                f.write("❌ Database file does not exist\n")
                return

            f.write("\n2. Testing SQLite connection...\n")
            try:
                conn = sqlite3.connect(db_path)
                f.write("✅ Connection successful\n")

                # Test integrity
                cursor = conn.execute("PRAGMA integrity_check;")
                integrity = cursor.fetchone()[0]
                f.write(f"Database integrity: {integrity}\n")

                # Test basic query
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                f.write(f"Tables: {[table[0] for table in tables]}\n")

                # Test game_sessions table
                cursor = conn.execute("SELECT COUNT(*) FROM game_sessions;")
                count = cursor.fetchone()[0]
                f.write(f"Sessions count: {count}\n")

                conn.close()
                f.write("✅ Connection closed successfully\n")

            except Exception as sqlite_error:
                f.write(f"❌ SQLite error: {sqlite_error}\n")
                f.write(f"Error type: {type(sqlite_error)}\n")
                f.write(f"Error args: {sqlite_error.args}\n")
                f.write(f"Error repr: {repr(sqlite_error)}\n")

                # Check if this is the mysterious "0" error
                if str(sqlite_error) == "0" or repr(sqlite_error) == "0":
                    f.write("🚨 Found the mysterious '0' error in SQLite!\n")

            f.write("\n3. Testing with row_factory...\n")
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT COUNT(*) FROM game_sessions;")
                count = cursor.fetchone()[0]
                f.write(f"✅ Row factory test successful, count: {count}\n")
                conn.close()

            except Exception as row_error:
                f.write(f"❌ Row factory error: {row_error}\n")
                f.write(f"Error type: {type(row_error)}\n")
                f.write(f"Error repr: {repr(row_error)}\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        f.write("\n" + "=" * 50 + "\n")
        f.write("SQLite test completed\n")


if __name__ == "__main__":
    test_sqlite()
    print("SQLite test completed. Check sqlite_test.txt for results.")
