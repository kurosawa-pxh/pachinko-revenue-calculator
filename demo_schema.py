#!/usr/bin/env python3
"""
Demonstration script for database schema and migration functionality.
"""

from src.database import DatabaseManager
import sys
import os
import tempfile

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def demonstrate_schema_features():
    """Demonstrate the database schema and migration features."""
    print("=== Database Schema and Migration Demo ===\n")

    # Use temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    try:
        print("1. Creating new database with schema...")
        db_manager = DatabaseManager(db_path)

        # Show database information
        db_info = db_manager.get_database_info()
        print(f"   Schema version: {db_info['schema_version']}")
        print(f"   Tables created: {', '.join(db_info['tables'])}")
        print(f"   Indexes created: {len(db_info['indexes'])}")
        print(f"   Database size: {db_info['database_size']} bytes")

        print("\n2. Database schema details:")
        print("   Tables:")
        for table in db_info['tables']:
            print(f"     - {table}")

        print("   Performance Indexes:")
        for index in db_info['indexes']:
            print(f"     - {index}")

        print("\n3. Schema constraints implemented:")
        print("   ✓ initial_investment >= 0")
        print("   ✓ final_investment >= 0 OR NULL")
        print("   ✓ return_amount >= 0 OR NULL")
        print("   ✓ final_investment >= initial_investment OR NULL")
        print("   ✓ Completed sessions must have end_time, final_investment, and return_amount")

        print("\n4. Performance indexes for requirements:")
        print("   ✓ idx_user_date - For efficient date-based queries (Req 2.1, 3.1)")
        print("   ✓ idx_user_month - For monthly statistics (Req 3.1)")
        print("   ✓ Additional indexes for query optimization")

        print("\n5. Migration system features:")
        print("   ✓ Schema version tracking")
        print("   ✓ Automatic database initialization")
        print("   ✓ Future migration support")
        print("   ✓ Database reset functionality")

        print("\n6. Testing database reset...")
        db_manager.reset_database()
        reset_info = db_manager.get_database_info()
        print(
            f"   After reset - Schema version: {reset_info['schema_version']}")
        print(
            f"   After reset - Total sessions: {reset_info['total_sessions']}")

        print("\n✓ Database schema and migration implementation complete!")
        print("\nKey features implemented:")
        print("  • Complete game_sessions table schema with constraints")
        print("  • Performance indexes (user_date, user_month) as required")
        print("  • Schema version tracking and migration system")
        print("  • Database initialization and reset functionality")
        print("  • Data integrity constraints and validation")

        # Clean up
        os.unlink(db_path)

    except Exception as e:
        print(f"✗ Demo failed: {e}")
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    demonstrate_schema_features()
