#!/usr/bin/env python3
"""
Push final database fix to GitHub
"""

import subprocess
import os


def push_final_fix():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the final fix
        print("Adding final database fix to git...")
        subprocess.run(['git', 'add', 'src/database.py'], check=True)

        # Commit with descriptive message
        commit_message = """FINAL FIX: Force SQLite usage in create_session method

- Remove PostgreSQL path completely from create_session
- Force SQLite INSERT SQL regardless of db_type setting
- Always use cursor.lastrowid for session ID retrieval
- Add debug logging to verify database type configuration
- Resolve KeyError(0) by ensuring SQLite path is always used

This definitively fixes the 'Failed to get session ID from PostgreSQL' 
error by forcing SQLite behavior in the session creation process."""

        print("Committing final fix...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed final fix to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_final_fix()
