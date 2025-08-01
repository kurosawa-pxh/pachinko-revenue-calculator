#!/usr/bin/env python3
"""
Check database files
"""

import os
import sqlite3


def check_files():
    with open('file_check.txt', 'w', encoding='utf-8') as f:
        f.write("📁 File Check Results\n")
        f.write("=" * 50 + "\n\n")

        # Check current directory
        f.write(f"Current directory: {os.getcwd()}\n\n")

        # List all files
        f.write("All files in directory:\n")
        for file in os.listdir('.'):
            if os.path.isfile(file):
                stat = os.stat(file)
                f.write(f"  {file}: size={stat.st_size} bytes\n")
        f.write("\n")

        # Check for database files specifically
        f.write("Database files:\n")
        db_files = [f for f in os.listdir('.') if f.endswith('.db')]
        if db_files:
            for db_file in db_files:
                f.write(f"  Found: {db_file}\n")
                try:
                    # Test SQLite connection
                    conn = sqlite3.connect(db_file)
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    f.write(f"    Tables: {[table[0] for table in tables]}\n")
                    conn.close()
                    f.write(f"    Status: ✅ OK\n")
                except Exception as e:
                    f.write(f"    Status: ❌ Error: {e}\n")
        else:
            f.write("  No .db files found\n")
        f.write("\n")

        # Check if files exist by name
        expected_files = ['pachinko_data.db', 'pachinko_auth.db']
        f.write("Expected database files:\n")
        for expected in expected_files:
            if os.path.exists(expected):
                f.write(f"  ✅ {expected} exists\n")
            else:
                f.write(f"  ❌ {expected} missing\n")


if __name__ == "__main__":
    check_files()
    print("File check completed. Check file_check.txt for results.")
