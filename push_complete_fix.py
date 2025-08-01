#!/usr/bin/env python3
"""
Push complete SQLite fix to GitHub
"""

import subprocess
import os


def push_complete_fix():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the complete fix
        print("Adding complete SQLite fix to git...")
        subprocess.run(['git', 'add', 'src/database.py'], check=True)

        # Commit with descriptive message
        commit_message = """COMPLETE FIX: Force SQLite-only database operations

- Force db_type to 'sqlite' regardless of configuration
- Remove all PostgreSQL connection paths from _get_connection
- Simplify connection cleanup to SQLite-only
- Eliminate PostgreSQL/SQLite branching completely
- Ensure consistent SQLite behavior throughout application

This definitively resolves the psycopg2.errors.SyntaxError by
completely removing PostgreSQL code paths and forcing SQLite usage."""

        print("Committing complete fix...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed complete fix to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_complete_fix()
