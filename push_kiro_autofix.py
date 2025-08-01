#!/usr/bin/env python3
"""
Push Kiro IDE autofix to GitHub
"""

import subprocess
import os


def push_kiro_autofix():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the autofix changes
        print("Adding Kiro IDE autofix changes to git...")
        subprocess.run(['git', 'add', 'src/database.py'], check=True)

        # Commit with descriptive message
        commit_message = """Apply Kiro IDE autofix after SQLite-only database fix

- Apply automatic code formatting and optimization
- Maintain SQLite-only database connection logic
- Preserve complete database connection fixes
- Keep simplified connection management

This commit applies Kiro IDE's automatic formatting while
preserving the critical SQLite-only database implementation."""

        print("Committing Kiro IDE autofix...")
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
    push_kiro_autofix()
