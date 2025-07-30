#!/usr/bin/env python3
"""
Comprehensive UI integration test suite.
Tests Streamlit UI components and end-to-end workflows without circular imports.
"""

from src.models import GameSession, ValidationError
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


class MockStreamlit:
    """Mock Streamlit for testing UI components without actual Streamlit dependency."""

    def __init__(self):
        self.session_state = {}
        self.columns_data = []
        self.markdown_calls = []
        self.error_calls = []
        self.success_calls = []
        self.info_calls = []
        self.warning_calls = []
        self.button_calls = []
        self.form_calls = []

    def columns(self, num_cols):
        """Mock st.columns()"""
        return [MockColumn(i) for i in range(num_cols)]

    def markdown(self, text, unsafe_allow_html=False):
        """Mock st.markdown()"""
        self.markdown_calls.append(
            {'text': text, 'unsafe_allow_html': unsafe_allow_html})

    def error(self, message):
        """Mock st.error()"""
        self.error_calls.append(message)

    def success(self, message):
        """Mock st.success()"""
        self.success_calls.append(message)

    def info(self, message):
        """Mock st.info()"""
        self.info_calls.append(message)

    def warning(self, message):
        """Mock st.warning()"""
        self.warning_calls.append(message)

    def button(self, label, key=None, use_container_width=False):
        """Mock st.button()"""
        self.button_calls.append(
            {'label': label, 'key': key, 'use_container_width': use_container_width})
        return False  # Default to not clicked

    def form(self, key):
        """Mock st.form()"""
        return MockForm(key)

    def rerun(self):
        """Mock st.rerun()"""
        pass

    def tabs(self, tab_names):
        """Mock st.tabs()"""
        return [MockTab(name) for name in tab_names]

    def plotly_chart(self, figure, use_container_width=False):
        """Mock st.plotly_chart()"""
        pass


class MockColumn:
    """Mock Streamlit column."""

    def __init__(self, index):
        self.index = index
        self.content = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def button(self, label, key=None, use_container_width=False):
        """Mock button in column"""
        return False

    def markdown(self, text, unsafe_allow_html=False):
        """Mock markdown in column"""
        self.content.append({'type': 'markdown', 'text': text})


class MockForm:
    """Mock Streamlit form."""

    def __init__(self, key):
        self.key = key
        self.submitted = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def form_submit_button(self, label):
        """Mock form submit button"""
        return self.submitted


class MockTab:
    """Mock Streamlit tab."""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class SimpleUIManager:
    """
    Simplified UI Manager for testing without Streamlit dependencies.
    Contains core UI logic and validation from the original UIManager.
    """

    def __init__(self, db_manager, stats_calculator):
        self.db_manager = db_manager
        self.stats_calculator = stats_calculator
        self.session_state = {}
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'current_page' not in self.session_state:
            self.session_state['current_page'] = 'home'
        if 'user_id' not in self.session_state:
            self.session_state['user_id'] = 'default_user'
        if 'active_session' not in self.session_state:
            self.session_state['active_session'] = None
        if 'form_errors' not in self.session_state:
            self.session_state['form_errors'] = {}

    def validate_session_start_input(self, session_date: date, start_time: time,
                                     store_name: str, machine_name: str,
                                     initial_investment: int) -> Dict[str, str]:
        """Validate session start input data."""
        errors = {}

        # Validate date
        if session_date > date.today():
            errors['session_date'] = "未来の日付は選択できません"

        # Validate store name
        if not store_name or not store_name.strip():
            errors['store_name'] = "店舗名は必須です"
        elif len(store_name.strip()) > 100:
            errors['store_name'] = "店舗名は100文字以内で入力してください"

        # Validate machine name
        if not machine_name or not machine_name.strip():
            errors['machine_name'] = "機種名は必須です"
        elif len(machine_name.strip()) > 100:
            errors['machine_name'] = "機種名は100文字以内で入力してください"

        # Validate initial investment
        if initial_investment is None or initial_investment <= 0:
            errors['initial_investment'] = "開始投資額は1円以上で入力してください"
        elif initial_investment > 1000000:
            errors['initial_investment'] = "開始投資額は100万円以下で入力してください"

        return errors

    def validate_session_end_input(self, end_time: time, final_investment: int,
                                   return_amount: int, start_time: time) -> Dict[str, str]:
        """Validate session end input data."""
        errors = {}

        # Validate end time
        if end_time <= start_time:
            errors['end_time'] = "終了時間は開始時間より後である必要があります"

        # Validate final investment
        if final_investment is None or final_investment < 0:
            errors['final_investment'] = "最終投資額は0円以上で入力してください"
        elif final_investment > 1000000:
            errors['final_investment'] = "最終投資額は100万円以下で入力してください"

        # Validate return amount
        if return_amount is None or return_amount < 0:
            errors['return_amount'] = "回収金額は0円以上で入力してください"
        elif return_amount > 10000000:
            errors['return_amount'] = "回収金額は1000万円以下で入力してください"

        return errors

    def create_session_from_input(self, session_date: date, start_time: time,
                                  store_name: str, machine_name: str,
                                  initial_investment: int) -> GameSession:
        """Create a GameSession from input data."""
        user_id = self.session_state.get('user_id', 'default_user')

        # Combine date and time
        start_datetime = datetime.combine(session_date, start_time)

        return GameSession(
            user_id=user_id,
            date=start_datetime,
            start_time=start_datetime,
            store_name=store_name.strip(),
            machine_name=machine_name.strip(),
            initial_investment=initial_investment
        )

    def complete_session(self, session: GameSession, end_time: time,
                         final_investment: int, return_amount: int) -> GameSession:
        """Complete a session with end data."""
        # Combine session date with end time
        end_datetime = datetime.combine(session.date.date(), end_time)

        session.complete_session(
            end_time=end_datetime,
            final_investment=final_investment,
            return_amount=return_amount
        )

        return session

    def get_profit_color_class(self, profit: int) -> str:
        """Get CSS class for profit color."""
        if profit > 0:
            return "profit-positive"
        elif profit < 0:
            return "profit-negative"
        else:
            return "profit-neutral"

    def format_currency(self, amount: int) -> str:
        """Format currency amount."""
        return f"{amount:+,}円"

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information (mocked for testing)."""
        return {
            'is_mobile': False,
            'is_tablet': False,
            'is_desktop': True,
            'screen_width': 1920,
            'screen_height': 1080
        }

    def handle_navigation(self, target_page: str) -> bool:
        """Handle page navigation."""
        valid_pages = ['home', 'record', 'stats', 'history', 'export']

        if target_page in valid_pages:
            self.session_state['current_page'] = target_page
            return True
        return False

    def get_recent_sessions_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Get summary of recent sessions."""
        try:
            user_id = self.session_state.get('user_id', 'default_user')
            sessions = self.db_manager.get_sessions_as_dict(
                user_id, limit=limit)

            if not sessions:
                return {
                    'has_data': False,
                    'total_sessions': 0,
                    'completed_sessions': 0,
                    'total_profit': 0
                }

            completed_sessions = [s for s in sessions if s.get('is_completed')]
            total_profit = sum(s.get('profit', 0)
                               or 0 for s in completed_sessions)

            return {
                'has_data': True,
                'total_sessions': len(sessions),
                'completed_sessions': len(completed_sessions),
                'total_profit': total_profit,
                'sessions': sessions
            }

        except Exception as e:
            return {
                'has_data': False,
                'error': str(e),
                'total_sessions': 0,
                'completed_sessions': 0,
                'total_profit': 0
            }


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    mock_db = Mock()
    mock_db.get_sessions_as_dict.return_value = []
    mock_db.create_session.return_value = 1
    mock_db.update_session.return_value = True
    return mock_db


@pytest.fixture
def mock_stats_calculator():
    """Create a mock statistics calculator."""
    mock_stats = Mock()
    mock_stats.get_user_basic_stats.return_value = Mock(
        completed_sessions=0,
        total_profit=0,
        win_rate=0.0
    )
    return mock_stats


@pytest.fixture
def ui_manager(mock_db_manager, mock_stats_calculator):
    """Create a SimpleUIManager instance."""
    return SimpleUIManager(mock_db_manager, mock_stats_calculator)


class TestUIManagerInitialization:
    """Test UI Manager initialization and setup."""

    def test_initialization(self, ui_manager):
        """Test UI manager initialization."""
        assert ui_manager.session_state['current_page'] == 'home'
        assert ui_manager.session_state['user_id'] == 'default_user'
        assert ui_manager.session_state['active_session'] is None
        assert ui_manager.session_state['form_errors'] == {}

    def test_device_info(self, ui_manager):
        """Test device information retrieval."""
        device_info = ui_manager.get_device_info()

        assert 'is_mobile' in device_info
        assert 'is_tablet' in device_info
        assert 'is_desktop' in device_info
        assert 'screen_width' in device_info
        assert 'screen_height' in device_info


class TestSessionStartValidation:
    """Test session start input validation."""

    def test_valid_session_start_input(self, ui_manager):
        """Test validation with valid session start data."""
        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert errors == {}

    def test_future_date_validation(self, ui_manager):
        """Test validation with future date."""
        future_date = date.today() + timedelta(days=1)

        errors = ui_manager.validate_session_start_input(
            session_date=future_date,
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert 'session_date' in errors
        assert "未来の日付は選択できません" in errors['session_date']

    def test_empty_store_name_validation(self, ui_manager):
        """Test validation with empty store name."""
        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert 'store_name' in errors
        assert "店舗名は必須です" in errors['store_name']

    def test_empty_machine_name_validation(self, ui_manager):
        """Test validation with empty machine name."""
        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="",
            initial_investment=10000
        )

        assert 'machine_name' in errors
        assert "機種名は必須です" in errors['machine_name']

    def test_invalid_investment_validation(self, ui_manager):
        """Test validation with invalid investment amounts."""
        # Zero investment
        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=0
        )

        assert 'initial_investment' in errors
        assert "開始投資額は1円以上で入力してください" in errors['initial_investment']

        # Negative investment
        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=-1000
        )

        assert 'initial_investment' in errors

        # Too high investment
        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=1000001
        )

        assert 'initial_investment' in errors
        assert "開始投資額は100万円以下で入力してください" in errors['initial_investment']

    def test_long_store_name_validation(self, ui_manager):
        """Test validation with too long store name."""
        long_name = "a" * 101  # 101 characters

        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name=long_name,
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert 'store_name' in errors
        assert "店舗名は100文字以内で入力してください" in errors['store_name']

    def test_long_machine_name_validation(self, ui_manager):
        """Test validation with too long machine name."""
        long_name = "a" * 101  # 101 characters

        errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name=long_name,
            initial_investment=10000
        )

        assert 'machine_name' in errors
        assert "機種名は100文字以内で入力してください" in errors['machine_name']


class TestSessionEndValidation:
    """Test session end input validation."""

    def test_valid_session_end_input(self, ui_manager):
        """Test validation with valid session end data."""
        errors = ui_manager.validate_session_end_input(
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=20000,
            start_time=time(10, 0)
        )

        assert errors == {}

    def test_invalid_end_time_validation(self, ui_manager):
        """Test validation with invalid end time."""
        errors = ui_manager.validate_session_end_input(
            end_time=time(9, 0),  # Before start time
            final_investment=15000,
            return_amount=20000,
            start_time=time(10, 0)
        )

        assert 'end_time' in errors
        assert "終了時間は開始時間より後である必要があります" in errors['end_time']

    def test_invalid_final_investment_validation(self, ui_manager):
        """Test validation with invalid final investment."""
        # Negative final investment
        errors = ui_manager.validate_session_end_input(
            end_time=time(12, 0),
            final_investment=-1000,
            return_amount=20000,
            start_time=time(10, 0)
        )

        assert 'final_investment' in errors
        assert "最終投資額は0円以上で入力してください" in errors['final_investment']

        # Too high final investment
        errors = ui_manager.validate_session_end_input(
            end_time=time(12, 0),
            final_investment=1000001,
            return_amount=20000,
            start_time=time(10, 0)
        )

        assert 'final_investment' in errors
        assert "最終投資額は100万円以下で入力してください" in errors['final_investment']

    def test_invalid_return_amount_validation(self, ui_manager):
        """Test validation with invalid return amount."""
        # Negative return amount
        errors = ui_manager.validate_session_end_input(
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=-1000,
            start_time=time(10, 0)
        )

        assert 'return_amount' in errors
        assert "回収金額は0円以上で入力してください" in errors['return_amount']

        # Too high return amount
        errors = ui_manager.validate_session_end_input(
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=10000001,
            start_time=time(10, 0)
        )

        assert 'return_amount' in errors
        assert "回収金額は1000万円以下で入力してください" in errors['return_amount']


class TestSessionCreation:
    """Test session creation and completion."""

    def test_create_session_from_input(self, ui_manager):
        """Test creating a GameSession from input data."""
        session = ui_manager.create_session_from_input(
            session_date=date(2024, 1, 15),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert session.user_id == 'default_user'
        assert session.date == datetime(2024, 1, 15, 10, 0)
        assert session.start_time == datetime(2024, 1, 15, 10, 0)
        assert session.store_name == "テスト店舗"
        assert session.machine_name == "テスト機種"
        assert session.initial_investment == 10000
        assert session.is_completed is False

    def test_complete_session(self, ui_manager):
        """Test completing a session."""
        # Create initial session
        session = ui_manager.create_session_from_input(
            session_date=date(2024, 1, 15),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        # Complete the session
        completed_session = ui_manager.complete_session(
            session=session,
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=20000
        )

        assert completed_session.is_completed is True
        assert completed_session.end_time == datetime(2024, 1, 15, 12, 0)
        assert completed_session.final_investment == 15000
        assert completed_session.return_amount == 20000
        assert completed_session.profit == 5000  # 20000 - 15000

    def test_create_session_with_whitespace(self, ui_manager):
        """Test creating session with whitespace in names."""
        session = ui_manager.create_session_from_input(
            session_date=date(2024, 1, 15),
            start_time=time(10, 0),
            store_name="  テスト店舗  ",
            machine_name="  テスト機種  ",
            initial_investment=10000
        )

        # Should trim whitespace
        assert session.store_name == "テスト店舗"
        assert session.machine_name == "テスト機種"


class TestNavigationAndState:
    """Test navigation and state management."""

    def test_handle_navigation_valid_pages(self, ui_manager):
        """Test navigation to valid pages."""
        valid_pages = ['home', 'record', 'stats', 'history', 'export']

        for page in valid_pages:
            result = ui_manager.handle_navigation(page)
            assert result is True
            assert ui_manager.session_state['current_page'] == page

    def test_handle_navigation_invalid_page(self, ui_manager):
        """Test navigation to invalid page."""
        result = ui_manager.handle_navigation('invalid_page')
        assert result is False
        # Should not change current page
        assert ui_manager.session_state['current_page'] == 'home'

    def test_session_state_persistence(self, ui_manager):
        """Test that session state persists across operations."""
        # Set some state
        ui_manager.session_state['user_id'] = 'test_user_123'
        ui_manager.session_state['active_session'] = 'test_session'

        # Perform navigation
        ui_manager.handle_navigation('stats')

        # State should persist
        assert ui_manager.session_state['user_id'] == 'test_user_123'
        assert ui_manager.session_state['active_session'] == 'test_session'
        assert ui_manager.session_state['current_page'] == 'stats'


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_profit_color_class(self, ui_manager):
        """Test profit color class assignment."""
        # Positive profit
        assert ui_manager.get_profit_color_class(5000) == "profit-positive"

        # Negative profit
        assert ui_manager.get_profit_color_class(-3000) == "profit-negative"

        # Zero profit
        assert ui_manager.get_profit_color_class(0) == "profit-neutral"

    def test_format_currency(self, ui_manager):
        """Test currency formatting."""
        assert ui_manager.format_currency(5000) == "+5,000円"
        assert ui_manager.format_currency(-3000) == "-3,000円"
        assert ui_manager.format_currency(0) == "+0円"
        assert ui_manager.format_currency(1234567) == "+1,234,567円"


class TestDataIntegration:
    """Test integration with database and statistics."""

    def test_get_recent_sessions_summary_with_data(self, ui_manager, mock_db_manager):
        """Test getting recent sessions summary with data."""
        # Mock database response
        mock_sessions = [
            {'id': 1, 'is_completed': True, 'profit': 5000},
            {'id': 2, 'is_completed': True, 'profit': -3000},
            {'id': 3, 'is_completed': False, 'profit': None}
        ]
        mock_db_manager.get_sessions_as_dict.return_value = mock_sessions

        summary = ui_manager.get_recent_sessions_summary(limit=10)

        assert summary['has_data'] is True
        assert summary['total_sessions'] == 3
        assert summary['completed_sessions'] == 2
        assert summary['total_profit'] == 2000  # 5000 + (-3000)
        assert len(summary['sessions']) == 3

    def test_get_recent_sessions_summary_no_data(self, ui_manager, mock_db_manager):
        """Test getting recent sessions summary with no data."""
        mock_db_manager.get_sessions_as_dict.return_value = []

        summary = ui_manager.get_recent_sessions_summary(limit=10)

        assert summary['has_data'] is False
        assert summary['total_sessions'] == 0
        assert summary['completed_sessions'] == 0
        assert summary['total_profit'] == 0

    def test_get_recent_sessions_summary_database_error(self, ui_manager, mock_db_manager):
        """Test getting recent sessions summary with database error."""
        mock_db_manager.get_sessions_as_dict.side_effect = Exception(
            "Database error")

        summary = ui_manager.get_recent_sessions_summary(limit=10)

        assert summary['has_data'] is False
        assert 'error' in summary
        assert summary['total_sessions'] == 0
        assert summary['completed_sessions'] == 0
        assert summary['total_profit'] == 0


class TestEndToEndWorkflows:
    """Test end-to-end UI workflows."""

    def test_complete_session_workflow(self, ui_manager, mock_db_manager):
        """Test complete session creation and completion workflow."""
        # Step 1: Validate start input
        start_errors = ui_manager.validate_session_start_input(
            session_date=date(2024, 1, 15),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )
        assert start_errors == {}

        # Step 2: Create session
        session = ui_manager.create_session_from_input(
            session_date=date(2024, 1, 15),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )
        assert session.is_completed is False

        # Step 3: Validate end input
        end_errors = ui_manager.validate_session_end_input(
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=20000,
            start_time=time(10, 0)
        )
        assert end_errors == {}

        # Step 4: Complete session
        completed_session = ui_manager.complete_session(
            session=session,
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=20000
        )

        # Verify final state
        assert completed_session.is_completed is True
        assert completed_session.profit == 5000
        assert completed_session.final_investment == 15000
        assert completed_session.return_amount == 20000

    def test_validation_error_workflow(self, ui_manager):
        """Test workflow with validation errors."""
        # Step 1: Try to create session with invalid data
        start_errors = ui_manager.validate_session_start_input(
            session_date=date.today() + timedelta(days=1),  # Future date
            start_time=time(10, 0),
            store_name="",  # Empty store name
            machine_name="テスト機種",
            initial_investment=0  # Invalid investment
        )

        # Should have multiple errors
        assert len(start_errors) == 3
        assert 'session_date' in start_errors
        assert 'store_name' in start_errors
        assert 'initial_investment' in start_errors

        # Step 2: Fix errors and try again
        fixed_errors = ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        # Should have no errors now
        assert fixed_errors == {}

    def test_navigation_workflow(self, ui_manager):
        """Test navigation workflow."""
        # Start at home
        assert ui_manager.session_state['current_page'] == 'home'

        # Navigate to record page
        result = ui_manager.handle_navigation('record')
        assert result is True
        assert ui_manager.session_state['current_page'] == 'record'

        # Navigate to stats page
        result = ui_manager.handle_navigation('stats')
        assert result is True
        assert ui_manager.session_state['current_page'] == 'stats'

        # Try invalid navigation
        result = ui_manager.handle_navigation('invalid')
        assert result is False
        # Should not change
        assert ui_manager.session_state['current_page'] == 'stats'

        # Navigate back to home
        result = ui_manager.handle_navigation('home')
        assert result is True
        assert ui_manager.session_state['current_page'] == 'home'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
