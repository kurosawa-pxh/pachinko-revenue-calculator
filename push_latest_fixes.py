#!/usr/bin/env python3
"""
Push latest database debugging fixes to GitHub
"""

import subprocess
import os


def push_latest_fixes():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the database debugging fixes
        print("Adding latest database debugging fixes to git...")
        subprocess.run(['git', 'add', 'src/database.py'], check=True)

        # Commit with descriptive message
        commit_message = """Add comprehensive database debugging and error handling

- Add detailed debug logging for session creation process
- Add database type verification in create_session method
- Add INSERT SQL logging for troubleshooting
- Improve error handling for both PostgreSQL and SQLite paths
- Add session ID retrieval debugging with proper error messages
- Add validation for SQLite lastrowid results

This addresses the KeyError(0) issue by providing detailed debugging
information and more robust error handling during session creation."""

        print("Committing latest fixes...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed latest fixes to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_latest_fixes()
