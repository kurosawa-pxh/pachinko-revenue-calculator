#!/usr/bin/env python3
"""
Push changes to GitHub
"""

import subprocess
import os


def push_changes():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the important files
        print("Adding files to git...")
        subprocess.run(['git', 'add', 'src/pachinko_app.py'], check=True)

        # Commit with descriptive message
        commit_message = """Fix database connection error and improve app initialization

- Fix DatabaseManager initialization conflict between db_path and config
- Remove redundant db_path parameter in PachinkoApp initialization
- Resolve 'Database connection error: 0' issue
- Ensure proper component initialization order
- Add psutil dependency support

This fixes the critical database connection issues that were preventing
the application from working properly after the previous date field fixes."""

        print("Committing changes...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed changes to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_changes()
