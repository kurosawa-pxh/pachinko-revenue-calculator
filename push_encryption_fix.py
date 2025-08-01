#!/usr/bin/env python3
"""
Push encryption fix to GitHub
"""

import subprocess
import os


def push_encryption_fix():
    try:
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Add the encryption fix
        print("Adding encryption fix to git...")
        subprocess.run(['git', 'add', 'src/config.py'], check=True)

        # Commit with descriptive message
        commit_message = """Fix dashboard display by disabling encryption in development

- Change default ENABLE_ENCRYPTION from 'true' to 'false'
- Resolve Base64 encoded text display issue in dashboard
- Ensure store names and machine names display as plain text
- Maintain encryption capability for production use

This fixes the dashboard showing encrypted Base64 strings like:
🏪 Z0FBQUFBQm9peVQ2STBwNVcxX0tLTjhRd2V2RC1obHhTZ3BuOC1XLW83c0ZxYWRYTG93eUM2WVNXVnFqckIwZUdTclZuUTM2eUtyUVl1TTdiTGlUYWZXNlhVMjU3NVdWS3c9PQ==
🎰 Z0FBQUFBQm9peVQ2Q1dvZGtaNl9xUE9WT3kxdzVTVEFXV1dMVFY0OU02bEVWaDNfS0pQZjhEMmZiNGR3SmpUNzh5T3lpcEw0QTRqYUpLZFJHUjFwSWU0aDdDRnQ2N1UwM3c9PQ=="""

        print("Committing encryption fix...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)

        # Push to GitHub
        print("Pushing to GitHub...")
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)

        print("✅ Successfully pushed encryption fix to GitHub!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    push_encryption_fix()
