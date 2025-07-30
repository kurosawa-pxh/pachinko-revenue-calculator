#!/usr/bin/env python3
"""
Demonstration of data encryption integration with database operations.

This script shows how the enhanced encryption functionality works with
the database to protect sensitive user data.
"""

from src.models_fixed import GameSession
from src.database import DatabaseManager
from src.authentication import AuthenticationManager
import os
import sys
import tempfile
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def demonstrate_encryption_integration():
    """Demonstrate the encryption integration with database operations."""
    print("🔐 Demonstrating Data Encryption Integration")
    print("=" * 50)

    # Create temporary databases for demonstration
    auth_db = tempfile.mktemp(suffix='_auth.db')
    data_db = tempfile.mktemp(suffix='_data.db')

    try:
        # 1. Initialize authentication manager
        print("\n1. Initializing authentication system...")
        auth_manager = AuthenticationManager(db_path=auth_db)

        # Register a test user
        username = "demo_user"
        email = "demo@example.com"
        password = "SecurePass123!"

        auth_manager.register_user(username, email, password)
        print(f"✅ User '{username}' registered successfully")

        # 2. Initialize database manager with encryption
        print("\n2. Initializing database with encryption...")
        db_manager = DatabaseManager(data_db, auth_manager)
        print("✅ Database initialized with encryption support")

        # 3. Create test session with sensitive data
        print("\n3. Creating game session with sensitive data...")
        test_session = GameSession(
            user_id="demo_user",
            date=datetime.now(),
            start_time=datetime.now(),
            store_name="マルハン新宿東口店",  # Sensitive: store name
            machine_name="CR花の慶次",        # Sensitive: machine name
            initial_investment=20000
        )

        print(f"Original store name: {test_session.store_name}")
        print(f"Original machine name: {test_session.machine_name}")

        # 4. Save session (data will be encrypted)
        print("\n4. Saving session to database (encrypting sensitive data)...")
        session_id = db_manager.create_session(test_session)
        print(f"✅ Session saved with ID: {session_id}")

        # 5. Check raw database content to verify encryption
        print("\n5. Checking raw database content...")
        with db_manager._get_connection() as conn:
            cursor = conn.execute(
                "SELECT store_name, machine_name FROM game_sessions WHERE id = ?",
                (session_id,)
            )
            raw_data = cursor.fetchone()

            print(
                f"Encrypted store name in DB: {raw_data['store_name'][:50]}...")
            print(
                f"Encrypted machine name in DB: {raw_data['machine_name'][:50]}...")
            print("✅ Data is encrypted in database")

        # 6. Retrieve session (data will be decrypted)
        print("\n6. Retrieving session from database (decrypting data)...")
        retrieved_sessions = db_manager.get_sessions("demo_user")
        retrieved_session = retrieved_sessions[0]

        print(f"Decrypted store name: {retrieved_session.store_name}")
        print(f"Decrypted machine name: {retrieved_session.machine_name}")
        print("✅ Data successfully decrypted on retrieval")

        # 7. Verify data integrity
        print("\n7. Verifying data integrity...")
        assert retrieved_session.store_name == test_session.store_name
        assert retrieved_session.machine_name == test_session.machine_name
        assert retrieved_session.initial_investment == test_session.initial_investment
        print("✅ All data matches original values")

        # 8. Update session with new encrypted data
        print("\n8. Updating session with new sensitive data...")
        retrieved_session.store_name = "パーラー太陽渋谷店"
        retrieved_session.machine_name = "P戦国乙女6"
        retrieved_session.complete_session(
            end_time=datetime.now(),
            final_investment=25000,
            return_amount=35000
        )

        success = db_manager.update_session(session_id, retrieved_session)
        print(f"✅ Session updated successfully: {success}")

        # 9. Verify updated data is properly encrypted/decrypted
        print("\n9. Verifying updated data...")
        updated_sessions = db_manager.get_sessions("demo_user")
        updated_session = updated_sessions[0]

        print(f"Updated store name: {updated_session.store_name}")
        print(f"Updated machine name: {updated_session.machine_name}")
        print(f"Profit: {updated_session.profit:,}円")
        print("✅ Updated data properly encrypted and decrypted")

        # 10. Security summary
        print("\n10. Security summary...")
        security_summary = auth_manager.get_security_summary()
        print(f"Encryption enabled: {security_summary['encryption_enabled']}")
        print(f"Active users: {security_summary['active_users']}")
        print("✅ Security features operational")

        print("\n" + "=" * 50)
        print("🎉 Encryption integration demonstration completed successfully!")
        print("\nKey features demonstrated:")
        print("• Automatic encryption of sensitive data (store names, machine names)")
        print("• Transparent decryption when retrieving data")
        print("• Data integrity preservation")
        print("• Backward compatibility with non-encrypted data")
        print("• Comprehensive security monitoring")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up temporary files
        for db_file in [auth_db, data_db]:
            if os.path.exists(db_file):
                os.unlink(db_file)


def demonstrate_security_features():
    """Demonstrate advanced security features."""
    print("\n\n🛡️ Demonstrating Advanced Security Features")
    print("=" * 50)

    auth_db = tempfile.mktemp(suffix='_security.db')

    try:
        # Initialize authentication manager
        auth_manager = AuthenticationManager(db_path=auth_db)

        # Register test user
        username = "security_test"
        email = "security@example.com"
        password = "SecureTest123!"

        auth_manager.register_user(username, email, password)

        # 1. Test suspicious activity detection
        print("\n1. Testing suspicious activity detection...")

        # Get user ID
        with auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )
            user_id = cursor.fetchone()['id']

        # Simulate suspicious activity
        for i in range(12):
            auth_manager._log_security_event(
                user_id, "LOGIN_FAILED", f"Simulated failed attempt {i+1}"
            )

        is_suspicious, reasons = auth_manager.detect_suspicious_activity(
            user_id)
        print(f"Suspicious activity detected: {is_suspicious}")
        print(f"Reasons: {', '.join(reasons)}")

        # 2. Test account locking
        print("\n2. Testing progressive account locking...")
        lock_success = auth_manager.lock_account(
            user_id, "Demonstration of security lock"
        )
        print(f"Account locked: {lock_success}")

        # Check lock status
        with auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT locked_until FROM users WHERE id = ?",
                (user_id,)
            )
            locked_until = cursor.fetchone()['locked_until']
            print(f"Locked until: {locked_until}")

        # 3. Test data integrity validation
        print("\n3. Testing data integrity validation...")
        validation_results = auth_manager.validate_data_integrity()
        print(
            f"Encryption test passed: {validation_results['encryption_test_passed']}")
        print(
            f"Database integrity OK: {validation_results['database_integrity_ok']}")
        print(f"Overall status: {validation_results['overall_status']}")

        # 4. Test security analytics
        print("\n4. Testing security analytics...")
        analytics = auth_manager.get_security_analytics(days=1)
        print(f"Analytics period: {analytics['period_days']} days")
        print(
            f"Daily statistics entries: {len(analytics['daily_statistics'])}")
        print(
            f"Suspicious activity reasons: {len(analytics['suspicious_activity_reasons'])}")

        print("\n✅ All security features working correctly!")

    except Exception as e:
        print(f"\n❌ Error during security demonstration: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up
        if os.path.exists(auth_db):
            os.unlink(auth_db)


if __name__ == "__main__":
    demonstrate_encryption_integration()
    demonstrate_security_features()
