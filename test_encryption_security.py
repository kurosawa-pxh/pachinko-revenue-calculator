#!/usr/bin/env python3
"""
Test script for enhanced encryption and security features.

Tests the data encryption functionality and suspicious activity detection
implemented in task 10.2.
"""

from src.authentication import AuthenticationManager, SecurityError, AuthenticationError
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestEncryptionSecurity(unittest.TestCase):
    """Test cases for encryption and security features."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # Initialize authentication manager with test database
        self.auth_manager = AuthenticationManager(db_path=self.temp_db.name)

        # Create test user
        self.test_username = "testuser"
        self.test_email = "test@example.com"
        self.test_password = "TestPass123!"

        self.auth_manager.register_user(
            self.test_username,
            self.test_email,
            self.test_password
        )

    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_basic_data_encryption(self):
        """Test basic data encryption and decryption."""
        # Test data
        test_data = "パチンコ店舗名テスト"

        # Encrypt data
        encrypted_data = self.auth_manager.encrypt_data(test_data)
        self.assertIsInstance(encrypted_data, str)
        self.assertNotEqual(encrypted_data, test_data)

        # Decrypt data
        decrypted_data = self.auth_manager.decrypt_data(encrypted_data)
        self.assertEqual(decrypted_data, test_data)

    def test_empty_data_encryption(self):
        """Test encryption of empty data."""
        # Test empty string
        encrypted_empty = self.auth_manager.encrypt_data("")
        self.assertEqual(encrypted_empty, "")

        decrypted_empty = self.auth_manager.decrypt_data("")
        self.assertEqual(decrypted_empty, "")

    def test_user_data_encryption(self):
        """Test encryption of user data dictionary."""
        # Test user data with sensitive fields
        user_data = {
            'user_id': 'user123',
            'store_name': 'テストパチンコ店',
            'machine_name': 'CR花の慶次',
            'initial_investment': 10000,
            'user_notes': '今日は調子が良い',
            'non_sensitive_field': 'this should not be encrypted'
        }

        # Encrypt user data
        encrypted_data = self.auth_manager.encrypt_user_data(user_data)

        # Check that sensitive fields are encrypted
        self.assertNotEqual(
            encrypted_data['store_name'], user_data['store_name'])
        self.assertNotEqual(
            encrypted_data['machine_name'], user_data['machine_name'])
        self.assertNotEqual(
            encrypted_data['user_notes'], user_data['user_notes'])

        # Check that non-sensitive fields are not encrypted
        self.assertEqual(encrypted_data['user_id'], user_data['user_id'])
        self.assertEqual(
            encrypted_data['initial_investment'], user_data['initial_investment'])
        self.assertEqual(
            encrypted_data['non_sensitive_field'], user_data['non_sensitive_field'])

        # Check encryption flags
        self.assertTrue(encrypted_data.get('store_name_encrypted', False))
        self.assertTrue(encrypted_data.get('machine_name_encrypted', False))
        self.assertTrue(encrypted_data.get('user_notes_encrypted', False))

        # Decrypt user data
        decrypted_data = self.auth_manager.decrypt_user_data(encrypted_data)

        # Check that sensitive fields are decrypted correctly
        self.assertEqual(decrypted_data['store_name'], user_data['store_name'])
        self.assertEqual(
            decrypted_data['machine_name'], user_data['machine_name'])
        self.assertEqual(decrypted_data['user_notes'], user_data['user_notes'])

        # Check that encryption flags are removed
        self.assertNotIn('store_name_encrypted', decrypted_data)
        self.assertNotIn('machine_name_encrypted', decrypted_data)
        self.assertNotIn('user_notes_encrypted', decrypted_data)

    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection."""
        # Get user ID
        with self.auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (self.test_username,)
            )
            user_id = cursor.fetchone()['id']

        # Test normal activity (should not be suspicious)
        is_suspicious, reasons = self.auth_manager.detect_suspicious_activity(
            user_id, "192.168.1.100", "Mozilla/5.0 (normal browser)"
        )
        self.assertFalse(is_suspicious)
        self.assertEqual(len(reasons), 0)

        # Simulate rapid login attempts
        for i in range(12):
            self.auth_manager._log_security_event(
                user_id, "LOGIN_FAILED", f"Failed attempt {i+1}"
            )

        # Check for suspicious activity
        is_suspicious, reasons = self.auth_manager.detect_suspicious_activity(
            user_id)
        self.assertTrue(is_suspicious)
        self.assertIn("短時間での大量ログイン試行", reasons)

    def test_account_locking_progressive(self):
        """Test progressive account locking."""
        # Get user ID
        with self.auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (self.test_username,)
            )
            user_id = cursor.fetchone()['id']

        # Test first lock (should be 30 minutes)
        success = self.auth_manager.lock_account(user_id, "Test lock 1")
        self.assertTrue(success)

        # Check that account is locked
        with self.auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT locked_until FROM users WHERE id = ?",
                (user_id,)
            )
            locked_until = cursor.fetchone()['locked_until']
            self.assertIsNotNone(locked_until)

        # Test unlock
        success = self.auth_manager.unlock_account(
            user_id, admin_override=True)
        self.assertTrue(success)

        # Check that account is unlocked
        with self.auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT locked_until FROM users WHERE id = ?",
                (user_id,)
            )
            locked_until = cursor.fetchone()['locked_until']
            self.assertIsNone(locked_until)

    def test_enhanced_login_security(self):
        """Test enhanced login with suspicious activity detection."""
        # Test normal login
        success, user_info = self.auth_manager.login_user(
            self.test_username, self.test_password
        )
        self.assertTrue(success)
        self.assertIn('security_warnings', user_info)

        # Test failed login with suspicious activity simulation
        # First, create some suspicious activity
        with self.auth_manager._get_auth_connection() as conn:
            cursor = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (self.test_username,)
            )
            user_id = cursor.fetchone()['id']

        # Simulate multiple failed attempts
        for i in range(4):
            try:
                self.auth_manager.login_user(
                    self.test_username, "wrong_password")
            except AuthenticationError:
                pass  # Expected to fail

        # Next attempt should trigger account lock due to failed attempts
        with self.assertRaises(AuthenticationError) as context:
            self.auth_manager.login_user(self.test_username, "wrong_password")

        self.assertIn("アカウントがロックされました", str(context.exception))

    def test_database_encryption_integration(self):
        """Test integration of encryption with database operations."""
        from src.database import DatabaseManager
        from src.models_fixed import GameSession
        from datetime import datetime

        # Create temporary database for testing
        temp_db_path = tempfile.mktemp(suffix='_db_test.db')

        try:
            # Initialize database manager with encryption
            db_manager = DatabaseManager(temp_db_path, self.auth_manager)

            # Create test session with sensitive data
            test_session = GameSession(
                user_id="test_user",
                date=datetime.now(),
                start_time=datetime.now(),
                store_name="テストパチンコ店舗",
                machine_name="CR花の慶次",
                initial_investment=10000
            )

            # Create session in database (should encrypt sensitive data)
            session_id = db_manager.create_session(test_session)
            self.assertIsInstance(session_id, int)

            # Verify data is encrypted in database by checking raw data
            with db_manager._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT store_name, machine_name FROM game_sessions WHERE id = ?",
                    (session_id,)
                )
                raw_data = cursor.fetchone()

                # The stored data should be different from original (encrypted)
                self.assertNotEqual(raw_data['store_name'], "テストパチンコ店舗")
                self.assertNotEqual(raw_data['machine_name'], "CR花の慶次")

            # Retrieve session (should decrypt sensitive data)
            retrieved_sessions = db_manager.get_sessions("test_user")
            self.assertEqual(len(retrieved_sessions), 1)

            retrieved_session = retrieved_sessions[0]

            # Verify decrypted data matches original
            self.assertEqual(retrieved_session.store_name, "テストパチンコ店舗")
            self.assertEqual(retrieved_session.machine_name, "CR花の慶次")
            self.assertEqual(retrieved_session.initial_investment, 10000)

            # Test update with encryption
            retrieved_session.store_name = "更新されたパチンコ店"
            retrieved_session.machine_name = "P戦国乙女"

            success = db_manager.update_session(session_id, retrieved_session)
            self.assertTrue(success)

            # Verify updated data is properly encrypted and decrypted
            updated_sessions = db_manager.get_sessions("test_user")
            updated_session = updated_sessions[0]

            self.assertEqual(updated_session.store_name, "更新されたパチンコ店")
            self.assertEqual(updated_session.machine_name, "P戦国乙女")

        finally:
            # Clean up
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_security_summary(self):
        """Test security summary generation."""
        summary = self.auth_manager.get_security_summary()

        # Check required fields
        required_fields = [
            'active_users', 'failed_logins_24h', 'locked_accounts',
            'active_sessions', 'encryption_enabled', 'security_features'
        ]

        for field in required_fields:
            self.assertIn(field, summary)

        # Check security features
        features = summary['security_features']
        expected_features = [
            'data_encryption', 'suspicious_activity_detection',
            'progressive_account_locking', 'session_management', 'security_logging'
        ]

        for feature in expected_features:
            self.assertIn(feature, features)
            self.assertTrue(features[feature])

    def test_security_analytics(self):
        """Test security analytics generation."""
        analytics = self.auth_manager.get_security_analytics(days=7)

        # Check required fields
        required_fields = [
            'period_days', 'daily_statistics', 'suspicious_activity_reasons',
            'ip_address_statistics', 'user_activity_patterns', 'generated_at'
        ]

        for field in required_fields:
            self.assertIn(field, analytics)

        self.assertEqual(analytics['period_days'], 7)

    def test_data_integrity_validation(self):
        """Test data integrity validation."""
        validation_results = self.auth_manager.validate_data_integrity()

        # Check required fields
        required_fields = [
            'encryption_test_passed', 'database_integrity_ok',
            'security_logs_consistent', 'overall_status', 'issues_found'
        ]

        for field in required_fields:
            self.assertIn(field, validation_results)

        # For a fresh database, encryption test should pass
        self.assertTrue(validation_results['encryption_test_passed'])

    def test_encryption_error_handling(self):
        """Test encryption error handling."""
        # Test with invalid encrypted data
        with self.assertRaises(SecurityError):
            self.auth_manager.decrypt_data("invalid_encrypted_data")

    def test_japanese_text_encryption(self):
        """Test encryption of Japanese text."""
        japanese_texts = [
            "パチンコ店舗",
            "CR花の慶次",
            "今日は調子が良い感じです",
            "収支：+15,000円",
            "機種：Pフィーバー戦姫絶唱シンフォギア3"
        ]

        for text in japanese_texts:
            encrypted = self.auth_manager.encrypt_data(text)
            decrypted = self.auth_manager.decrypt_data(encrypted)
            self.assertEqual(decrypted, text, f"Failed for text: {text}")


def run_tests():
    """Run all tests."""
    print("🔒 Testing Enhanced Encryption and Security Features...")
    print("=" * 60)

    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestEncryptionSecurity)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All encryption and security tests passed!")
        print(f"✅ Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"❌ Failures: {len(result.failures)}")
        print(f"❌ Errors: {len(result.errors)}")

        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
