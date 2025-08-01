#!/usr/bin/env python3
"""
Debug database type configuration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def debug_db_type():
    with open('db_type_debug.txt', 'w', encoding='utf-8') as f:
        f.write("🔍 Database Type Debug\n")
        f.write("=" * 50 + "\n\n")

        try:
            from src.config import get_config
            from src.database import DatabaseManager

            f.write("1. Checking config...\n")
            config = get_config()
            db_config = config.get_database_config()
            f.write(f"Database config: {db_config}\n")
            f.write(f"Database type from config: {db_config.get('type')}\n\n")

            f.write("2. Checking DatabaseManager...\n")
            db_manager = DatabaseManager(config=config)
            f.write(f"DatabaseManager db_type: {db_manager.db_type}\n")
            f.write(f"DatabaseManager db_config: {db_manager.db_config}\n\n")

            f.write("3. Testing INSERT SQL generation...\n")
            # Check which INSERT SQL is being used
            if db_manager.db_type == 'postgresql':
                f.write("Using PostgreSQL INSERT SQL (with RETURNING)\n")
                insert_sql = """
                INSERT INTO game_sessions (
                    user_id, date, start_time, end_time, store_name, machine_name,
                    initial_investment, final_investment, return_amount, profit,
                    is_completed, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """
                f.write("This SQL expects RETURNING clause\n")
            else:
                f.write("Using SQLite INSERT SQL (without RETURNING)\n")
                insert_sql = """
                INSERT INTO game_sessions (
                    user_id, date, start_time, end_time, store_name, machine_name,
                    initial_investment, final_investment, return_amount, profit,
                    is_completed, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                f.write("This SQL uses lastrowid for ID\n")

            f.write(f"\nGenerated SQL:\n{insert_sql}\n")

            f.write("\n4. Testing actual database connection...\n")
            try:
                with db_manager._get_connection() as conn:
                    f.write("✅ Connection successful\n")

                    # Test the actual database type
                    try:
                        # This will work for SQLite
                        cursor = conn.execute("SELECT sqlite_version()")
                        version = cursor.fetchone()[0]
                        f.write(f"✅ SQLite version: {version}\n")
                        f.write("Database is actually SQLite\n")
                    except Exception as sqlite_test:
                        f.write(f"SQLite test failed: {sqlite_test}\n")

                        # Try PostgreSQL test
                        try:
                            cursor = conn.cursor()
                            cursor.execute("SELECT version()")
                            version = cursor.fetchone()[0]
                            f.write(f"✅ PostgreSQL version: {version}\n")
                            f.write("Database is actually PostgreSQL\n")
                        except Exception as pg_test:
                            f.write(f"PostgreSQL test failed: {pg_test}\n")

            except Exception as conn_error:
                f.write(f"❌ Connection failed: {conn_error}\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())

        f.write("\n" + "=" * 50 + "\n")
        f.write("Database type debug completed\n")


if __name__ == "__main__":
    debug_db_type()
    print("Database type debug completed. Check db_type_debug.txt for results.")
