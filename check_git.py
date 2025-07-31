#!/usr/bin/env python3
"""
Check git status and write to file
"""

import subprocess
import os


def check_git_status():
    try:
        # Change to the correct directory
        os.chdir('/Users/kurosawashun/Desktop/win-or-lose/pachinko-app')

        # Check git status
        result = subprocess.run(['git', 'status', '--porcelain'],
                                capture_output=True, text=True)

        with open('git_status.txt', 'w') as f:
            f.write("=== Git Status ===\n")
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"Stdout:\n{result.stdout}\n")
            f.write(f"Stderr:\n{result.stderr}\n")

            # Check remote
            remote_result = subprocess.run(['git', 'remote', '-v'],
                                           capture_output=True, text=True)
            f.write(f"\n=== Git Remote ===\n")
            f.write(f"Remote stdout:\n{remote_result.stdout}\n")

            # Check last commit
            log_result = subprocess.run(['git', 'log', '--oneline', '-1'],
                                        capture_output=True, text=True)
            f.write(f"\n=== Last Commit ===\n")
            f.write(f"Log stdout:\n{log_result.stdout}\n")

            # Check branch
            branch_result = subprocess.run(['git', 'branch'],
                                           capture_output=True, text=True)
            f.write(f"\n=== Current Branch ===\n")
            f.write(f"Branch stdout:\n{branch_result.stdout}\n")

        print("Git status written to git_status.txt")

    except Exception as e:
        with open('git_status.txt', 'w') as f:
            f.write(f"Error checking git status: {e}\n")
        print(f"Error: {e}")


if __name__ == "__main__":
    check_git_status()
