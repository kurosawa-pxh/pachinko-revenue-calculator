#!/usr/bin/env python3
"""
Test script for database initialization improvements.

Tests that the database initialization process works correctly
and doesn't produce "already exists" errors on repeated runs.
"""

from src.database import DatabaseManager
from src.authentication import AuthenticationManager
from src.config import get_config
import os
import sys
import logging
import sqlite3
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


# Add src directory to path
sys.path.append('src')


def setup_test_environment():
    """Setup test environment with temporary databases."""
    test_db_path = "test_pachinko_data.db"
    test_auth_db_path = "test_pachinko_auth.db"

    # Remove existing test databases
    for db_path in [test_db_path, test_auth_db_path]:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing test database: {db_path}")

    return test_db_path, test_auth_db_path


def test_database_initialization():
    """Test database manager initialization."""
    print("\n=== Testing Database Manager Initialization ===")

    test_db_path, _ = setup_test_environment()

    try:
        # First initialization
        print("1. First initialization...")
        config = get_config()
        db_manager1 = DatabaseManager(db_path=test_db_path, config=config)
        print("✅ First initialization successful")

        # Second initialization (should not cause errors)
        print("2. Second initialization...")
        db_manager2 = DatabaseManager(db_path=test_db_path, config=config)
        print("✅ Second initialization successful")

        # Third initialization (should not cause errors)
        print("3. Third initialization...")
        db_manager3 = DatabaseManager(db_path=test_db_path, config=config)
        print("✅ Third initialization successful")

        # Verify database structure
        print("4. Verifying database structure...")
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ['game_sessions', 'schema_version']
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")

        return True

    except Exception as e:
        print(f"❌ Database initialization test failed: {e}")
        return False

    finally:
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def test_auth_initialization():
    """Test authentication manager initialization."""
    print("\n=== Testing Authentication Manager Initialization ===")

    _, test_auth_db_path = setup_test_environment()

    try:
        # First initialization
        print("1. First initialization...")
        auth_manager1 = AuthenticationManager(db_path=test_auth_db_path)
        print("✅ First initialization successful")

        # Second initialization (should not cause errors)
        print("2. Second initialization...")
        auth_manager2 = AuthenticationManager(db_path=test_auth_db_path)
        print("✅ Second initialization successful")

        # Third initialization (should not cause errors)
        print("3. Third initialization...")
        auth_manager3 = AuthenticationManager(db_path=test_auth_db_path)
        print("✅ Third initialization successful")

        # Verify database structure
        print("4. Verifying authentication database structure...")
        with sqlite3.connect(test_auth_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ['users', 'user_sessions', 'security_logs']
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")

        return True

    except Exception as e:
        print(f"❌ Authentication initialization test failed: {e}")
        return False

    finally:
        # Cleanup
        if os.path.exists(test_auth_db_path):
            os.remove(test_auth_db_path)


def test_repeated_initialization():
    """Test repeated initialization in a loop."""
    print("\n=== Testing Repeated Initialization ===")

    test_db_path, test_auth_db_path = setup_test_environment()

    try:
        success_count = 0
        total_tests = 10

        for i in range(total_tests):
            try:
                # Initialize both managers
                config = get_config()
                db_manager = DatabaseManager(
                    db_path=test_db_path, config=config)
                auth_manager = AuthenticationManager(db_path=test_auth_db_path)

                success_count += 1
                print(f"✅ Iteration {i+1}/{total_tests} successful")

            except Exception as e:
                print(f"❌ Iteration {i+1}/{total_tests} failed: {e}")

        print(
            f"\nResults: {success_count}/{total_tests} successful initializations")
        return success_count == total_tests

    except Exception as e:
        print(f"❌ Repeated initialization test failed: {e}")
        return False

    finally:
        # Cleanup
        for db_path in [test_db_path, test_auth_db_path]:
            if os.path.exists(db_path):
                os.remove(db_path)


def main():
    """Run all initialization tests."""
    print("🎰 Pachinko Revenue Calculator - Initialization Tests")
    print("=" * 60)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run tests
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Authentication Initialization", test_auth_initialization),
        ("Repeated Initialization", test_repeated_initialization)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_function in tests:
        try:
            if test_function():
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All initialization tests passed!")
        print("✅ Database initialization improvements are working correctly")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
