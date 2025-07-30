"""
Test the history functionality implementation for task 5.1.
"""

import pytest
import tempfile
import os
from datetime import datetime, date, time
from src.database import DatabaseManager
from src.models_fixed import GameSession


def test_get_sessions_as_dict():
    """Test that get_sessions_as_dict returns proper dictionary format."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)

        # Create test session
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        # Save session
        session_id = db_manager.create_session(session)

        # Complete the session
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )
        db_manager.update_session(session_id, session)

        # Test get_sessions_as_dict
        sessions_dict = db_manager.get_sessions_as_dict("test_user")

        # Verify results
        assert len(sessions_dict) == 1
        session_dict = sessions_dict[0]

        # Check that it's a dictionary
        assert isinstance(session_dict, dict)

        # Check required fields
        assert session_dict['id'] == session_id
        assert session_dict['user_id'] == "test_user"
        assert session_dict['store_name'] == "テスト店舗"
        assert session_dict['machine_name'] == "テスト機種"
        assert session_dict['initial_investment'] == 10000
        assert session_dict['final_investment'] == 15000
        assert session_dict['return_amount'] == 20000
        assert session_dict['profit'] == 5000
        assert session_dict['is_completed'] == True

        # Check date fields are ISO format strings
        assert isinstance(session_dict['date'], str)
        assert isinstance(session_dict['start_time'], str)
        assert isinstance(session_dict['end_time'], str)

        print("✅ get_sessions_as_dict test passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_history_filtering():
    """Test that history filtering works correctly."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)

        # Create multiple test sessions
        sessions_data = [
            {
                'date': datetime(2024, 1, 15),
                'store': "マルハン新宿店",
                'machine': "CRシンフォギア",
                'investment': 10000,
                'completed': True
            },
            {
                'date': datetime(2024, 1, 16),
                'store': "ダイナム渋谷店",
                'machine': "CRエヴァンゲリオン",
                'investment': 15000,
                'completed': False
            },
            {
                'date': datetime(2024, 2, 1),
                'store': "マルハン新宿店",
                'machine': "CRシンフォギア",
                'investment': 12000,
                'completed': True
            }
        ]

        session_ids = []
        for data in sessions_data:
            session = GameSession(
                user_id="test_user",
                date=data['date'],
                start_time=data['date'].replace(hour=10),
                store_name=data['store'],
                machine_name=data['machine'],
                initial_investment=data['investment']
            )

            session_id = db_manager.create_session(session)
            session_ids.append(session_id)

            if data['completed']:
                session.complete_session(
                    end_time=data['date'].replace(hour=12),
                    final_investment=data['investment'] + 5000,
                    return_amount=data['investment'] + 3000
                )
                db_manager.update_session(session_id, session)

        # Test date range filtering
        jan_range = (datetime(2024, 1, 1), datetime(2024, 1, 31, 23, 59, 59))
        jan_sessions = db_manager.get_sessions_as_dict(
            "test_user", date_range=jan_range)
        assert len(jan_sessions) == 2

        # Test limit
        limited_sessions = db_manager.get_sessions_as_dict(
            "test_user", limit=1)
        assert len(limited_sessions) == 1

        print("✅ History filtering test passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_advanced_filtering():
    """Test advanced filtering functionality including profit/loss filters."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)

        # Create test sessions with different outcomes
        sessions_data = [
            {
                'date': datetime(2024, 1, 15),
                'store': "マルハン新宿店",
                'machine': "CRシンフォギア",
                'investment': 10000,
                'final_investment': 15000,
                'return_amount': 20000,  # Profit: +5000
                'completed': True
            },
            {
                'date': datetime(2024, 1, 16),
                'store': "ダイナム渋谷店",
                'machine': "CRエヴァンゲリオン",
                'investment': 15000,
                'final_investment': 20000,
                'return_amount': 10000,  # Loss: -10000
                'completed': True
            },
            {
                'date': datetime(2024, 1, 17),
                'store': "マルハン新宿店",
                'machine': "CRシンフォギア",
                'investment': 12000,
                'final_investment': 18000,
                'return_amount': 18000,  # Break-even: 0
                'completed': True
            },
            {
                'date': datetime(2024, 1, 18),
                'store': "パチンコ太郎",
                'machine': "CRワンピース",
                'investment': 8000,
                'completed': False  # Incomplete session
            }
        ]

        session_ids = []
        for data in sessions_data:
            session = GameSession(
                user_id="test_user",
                date=data['date'],
                start_time=data['date'].replace(hour=10),
                store_name=data['store'],
                machine_name=data['machine'],
                initial_investment=data['investment']
            )

            session_id = db_manager.create_session(session)
            session_ids.append(session_id)

            if data['completed']:
                session.complete_session(
                    end_time=data['date'].replace(hour=12),
                    final_investment=data['final_investment'],
                    return_amount=data['return_amount']
                )
                db_manager.update_session(session_id, session)

        # Test all sessions
        all_sessions = db_manager.get_sessions_as_dict("test_user")
        assert len(all_sessions) == 4

        # Test completed only filter
        completed_sessions = [
            s for s in all_sessions if s.get('is_completed', False)]
        assert len(completed_sessions) == 3

        # Test profit filter (winning sessions)
        winning_sessions = [
            s for s in completed_sessions if s.get('profit', 0) > 0]
        assert len(winning_sessions) == 1
        assert winning_sessions[0]['profit'] == 5000

        # Test loss filter (losing sessions)
        losing_sessions = [
            s for s in completed_sessions if s.get('profit', 0) < 0]
        assert len(losing_sessions) == 1
        assert losing_sessions[0]['profit'] == -10000

        # Test break-even filter
        breakeven_sessions = [
            s for s in completed_sessions if s.get('profit', 0) == 0]
        assert len(breakeven_sessions) == 1
        assert breakeven_sessions[0]['profit'] == 0

        # Test store name filter
        maruhan_sessions = [s for s in all_sessions
                            if 'マルハン' in s.get('store_name', '').lower()]
        assert len(maruhan_sessions) == 2

        # Test machine name filter
        symphogear_sessions = [s for s in all_sessions
                               if 'シンフォギア' in s.get('machine_name', '').lower()]
        assert len(symphogear_sessions) == 2

        print("✅ Advanced filtering test passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_no_data_scenarios():
    """Test scenarios where no data exists or filters return no results."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)

        # Test empty database
        sessions = db_manager.get_sessions_as_dict("test_user")
        assert len(sessions) == 0

        # Create one session
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        session_id = db_manager.create_session(session)

        # Test with date range that excludes the session
        future_range = (datetime(2024, 2, 1), datetime(2024, 2, 28))
        filtered_sessions = db_manager.get_sessions_as_dict(
            "test_user", date_range=future_range)
        assert len(filtered_sessions) == 0

        # Test with non-existent user
        no_user_sessions = db_manager.get_sessions_as_dict("nonexistent_user")
        assert len(no_user_sessions) == 0

        print("✅ No data scenarios test passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_sorting_functionality():
    """Test sorting functionality for history display."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name

    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)

        # Create test sessions with different dates and profits
        sessions_data = [
            {
                'date': datetime(2024, 1, 15),
                'investment': 10000,
                'final_investment': 15000,
                'return_amount': 20000,  # Profit: +5000
            },
            {
                'date': datetime(2024, 1, 10),
                'investment': 8000,
                'final_investment': 12000,
                'return_amount': 8000,   # Loss: -4000
            },
            {
                'date': datetime(2024, 1, 20),
                'investment': 20000,
                'final_investment': 25000,
                'return_amount': 30000,  # Profit: +5000
            }
        ]

        session_ids = []
        for i, data in enumerate(sessions_data):
            session = GameSession(
                user_id="test_user",
                date=data['date'],
                start_time=data['date'].replace(hour=10),
                store_name=f"店舗{i+1}",
                machine_name=f"機種{i+1}",
                initial_investment=data['investment']
            )

            session_id = db_manager.create_session(session)
            session_ids.append(session_id)

            session.complete_session(
                end_time=data['date'].replace(hour=12),
                final_investment=data['final_investment'],
                return_amount=data['return_amount']
            )
            db_manager.update_session(session_id, session)

        # Get all sessions
        all_sessions = db_manager.get_sessions_as_dict("test_user")
        assert len(all_sessions) == 3

        # Test date sorting (newest first - default)
        date_desc = sorted(all_sessions, key=lambda s: s.get(
            'date', ''), reverse=True)
        assert date_desc[0]['date'] == '2024-01-20T00:00:00'
        assert date_desc[1]['date'] == '2024-01-15T00:00:00'
        assert date_desc[2]['date'] == '2024-01-10T00:00:00'

        # Test date sorting (oldest first)
        date_asc = sorted(all_sessions, key=lambda s: s.get('date', ''))
        assert date_asc[0]['date'] == '2024-01-10T00:00:00'
        assert date_asc[1]['date'] == '2024-01-15T00:00:00'
        assert date_asc[2]['date'] == '2024-01-20T00:00:00'

        # Test profit sorting (highest first)
        profit_desc = sorted(
            all_sessions, key=lambda s: s.get('profit', 0), reverse=True)
        # Two sessions have +5000, but this tests the sorting works
        assert profit_desc[0]['profit'] == 5000
        assert profit_desc[2]['profit'] == -4000

        # Test investment sorting (highest first)
        investment_desc = sorted(all_sessions, key=lambda s: s.get(
            'final_investment', 0), reverse=True)
        assert investment_desc[0]['final_investment'] == 25000
        assert investment_desc[1]['final_investment'] == 15000
        assert investment_desc[2]['final_investment'] == 12000

        print("✅ Sorting functionality test passed!")

    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    test_get_sessions_as_dict()
    test_history_filtering()
    test_advanced_filtering()
    test_no_data_scenarios()
    test_sorting_functionality()
    print("🎉 All history functionality tests passed!")
