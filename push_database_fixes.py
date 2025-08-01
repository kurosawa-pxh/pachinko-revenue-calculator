#!/usr/bin/env python3
"""
Push database connection fixes to GitHub
"""

import subprocess
import os


def push_database_fixes():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the important database fixes
        print("Adding database fixes to git...")
        subprocess.run(['git', 'add', 'src/database.py'], check=True)

        # Commit with descriptive message
        commit_message = """Improve database connection error handling and debugging

- Add detailed error logging for database connection failures
- Add timeout parameter to SQLite connections (30 seconds)
- Add connection test to verify database accessibility
- Improve error reporting with type and args information
- Add debug logging for connection attempts and paths

This addresses the 'Database connection error: 0' issue by providing
better error information and more robust connection handling."""

        print("Committing database fixes...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed database fixes to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_database_fixes()
