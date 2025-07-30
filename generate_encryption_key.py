#!/usr/bin/env python3
"""
Generate a secure encryption key for the Pachinko Revenue Calculator.

This script generates a 32-character encryption key suitable for use
with the ENCRYPTION_KEY environment variable.
"""

import os
import secrets
from cryptography.fernet import Fernet


def generate_encryption_key():
    """Generate a secure 32-character encryption key."""

    print("🔐 Encryption Key Generator")
    print("=" * 50)

    # Method 1: Using Fernet (recommended for cryptography library)
    fernet_key = Fernet.generate_key()
    print(f"Fernet Key (Base64): {fernet_key.decode()}")

    # Method 2: 32-character hex string
    hex_key = os.urandom(32).hex()[:32]
    print(f"32-char Hex Key: {hex_key}")

    # Method 3: URL-safe base64 (32 characters)
    urlsafe_key = secrets.token_urlsafe(24)[:32]  # 24 bytes = 32 base64 chars
    print(f"URL-safe Key: {urlsafe_key}")

    print("\n📋 Streamlit Cloud設定用:")
    print(f'ENCRYPTION_KEY = "{fernet_key.decode()}"')

    print("\n⚠️ 重要な注意事項:")
    print("- このキーは安全に保管してください")
    print("- 本番環境では必ずこのキーを変更してください")
    print("- キーを紛失するとデータが復号化できなくなります")

    return fernet_key.decode()


if __name__ == "__main__":
    generate_encryption_key()
