#!/usr/bin/env python3
"""
Debug authentication system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def debug_auth():
    with open('auth_debug.txt', 'w', encoding='utf-8') as f:
        f.write("🔍 Authentication System Debug\n")
        f.write("=" * 50 + "\n\n")

        try:
            # Test imports
            f.write("1. Testing imports...\n")
            from src.authentication import AuthenticationManager
            f.write("✅ AuthenticationManager import successful\n\n")

            # Check if auth database exists
            f.write("2. Checking auth database file...\n")
            auth_db_path = "pachinko_auth.db"
            if os.path.exists(auth_db_path):
                f.write(f"✅ Auth database exists: {auth_db_path}\n")
            else:
                f.write(f"❌ Auth database missing: {auth_db_path}\n")
            f.write("\n")

            # Test AuthenticationManager creation
            f.write("3. Testing AuthenticationManager creation...\n")
            try:
                auth_manager = AuthenticationManager(db_path=auth_db_path)
                f.write("✅ AuthenticationManager created\n")

                # Test database initialization
                f.write("4. Testing database initialization...\n")
                if hasattr(auth_manager, '_initialize_auth_database'):
                    auth_manager._initialize_auth_database()
                    f.write("✅ Auth database initialized\n")
                else:
                    f.write("❌ _initialize_auth_database method not found\n")

                # Test user registration
                f.write("5. Testing user registration...\n")
                try:
                    result = auth_manager.register_user(
                        "test_user", "test@example.com", "password123")
                    f.write(f"Registration result: {result}\n")
                except Exception as reg_error:
                    f.write(f"❌ Registration failed: {reg_error}\n")

            except Exception as auth_error:
                f.write(
                    f"❌ AuthenticationManager creation failed: {auth_error}\n")
                import traceback
                f.write(traceback.format_exc())
                f.write("\n")

        except Exception as e:
            f.write(f"❌ Critical error: {e}\n")
            import traceback
            f.write(traceback.format_exc())
            f.write("\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("Auth debug completed\n")


if __name__ == "__main__":
    debug_auth()
    print("Auth debug completed. Check auth_debug.txt for results.")
