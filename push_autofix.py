#!/usr/bin/env python3
"""
Push Kiro IDE autofix to GitHub
"""

import subprocess
import os


def push_autofix():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the autofix changes
        print("Adding Kiro IDE autofix changes to git...")
        subprocess.run(['git', 'add', 'src/database.py'], check=True)

        # Commit with descriptive message
        commit_message = """Apply Kiro IDE autofix to database.py

- Apply automatic code formatting and style fixes
- Maintain SQLite-only session creation logic
- Preserve database connection error handling improvements
- Keep debug logging for troubleshooting

This commit applies Kiro IDE's automatic formatting while
preserving the critical SQLite-only fixes for session creation."""

        print("Committing autofix changes...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed Kiro IDE autofix to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_autofix()
