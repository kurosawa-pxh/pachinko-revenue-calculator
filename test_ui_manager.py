"""
Test suite for the UI Manager component.
"""

from src.database import DatabaseError
from src.models import ValidationError
from src.ui_manager import UIManager
import pytest
from datetime import date, time, datetime
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestUIManager:
    """Test cases for UIManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_manager = Mock()
        self.mock_stats_calculator = Mock()

        # Mock streamlit to avoid import issues in tests
        with patch('src.ui_manager.st'):
            self.ui_manager = UIManager(
                self.mock_db_manager, self.mock_stats_calculator)

    def test_validate_session_start_input_valid_data(self):
        """Test validation with valid session start data."""
        errors = self.ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert errors == {}

    def test_validate_session_start_input_empty_store_name(self):
        """Test validation with empty store name."""
        errors = self.ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert "store_name" in errors
        assert "店舗名は必須です" in errors["store_name"]

    def test_validate_session_start_input_empty_machine_name(self):
        """Test validation with empty machine name."""
        errors = self.ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="",
            initial_investment=10000
        )

        assert "machine_name" in errors
        assert "機種名は必須です" in errors["machine_name"]

    def test_validate_session_start_input_invalid_investment(self):
        """Test validation with invalid investment amount."""
        errors = self.ui_manager.validate_session_start_input(
            session_date=date.today(),
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=0
        )

        assert "initial_investment" in errors
        assert "開始投資額は1円以上で入力してください" in errors["initial_investment"]

    def test_validate_session_start_input_future_date(self):
        """Test validation with future date."""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=1)

        errors = self.ui_manager.validate_session_start_input(
            session_date=future_date,
            start_time=time(10, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000
        )

        assert "session_date" in errors
        assert "未来の日付は選択できません" in errors["session_date"]

    def test_validate_session_end_input_valid_data(self):
        """Test validation with valid session end data."""
        # Use yesterday's date to avoid future time validation issues
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        session_data = {
            'start_time': yesterday.replace(hour=10, minute=0).isoformat(),
            'initial_investment': 10000
        }

        errors = self.ui_manager.validate_session_end_input(
            session_data=session_data,
            end_time=time(12, 0),
            final_investment=15000,
            return_amount=20000
        )

        assert errors == {}

    def test_validate_session_end_input_invalid_end_time(self):
        """Test validation with invalid end time."""
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        session_data = {
            'start_time': yesterday.replace(hour=10, minute=0).isoformat(),
            'initial_investment': 10000
        }

        errors = self.ui_manager.validate_session_end_input(
            session_data=session_data,
            end_time=time(9, 0),  # Before start time
            final_investment=15000,
            return_amount=20000
        )

        assert "end_time" in errors
        assert "終了時間は開始時間より後である必要があります" in errors["end_time"]

    def test_validate_session_end_input_invalid_final_investment(self):
        """Test validation with invalid final investment."""
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        session_data = {
            'start_time': yesterday.replace(hour=10, minute=0).isoformat(),
            'initial_investment': 10000
        }

        errors = self.ui_manager.validate_session_end_input(
            session_data=session_data,
            end_time=time(12, 0),
            final_investment=5000,  # Less than initial investment
            return_amount=20000
        )

        assert "final_investment" in errors
        assert "最終投資額は開始投資額" in errors["final_investment"]

    def test_validate_numeric_input_valid(self):
        """Test numeric input validation with valid data."""
        error = self.ui_manager.validate_numeric_input(
            value=10000,
            field_name="テスト金額",
            min_value=0,
            max_value=100000
        )

        assert error is None

    def test_validate_numeric_input_below_minimum(self):
        """Test numeric input validation below minimum."""
        error = self.ui_manager.validate_numeric_input(
            value=-1000,
            field_name="テスト金額",
            min_value=0,
            max_value=100000
        )

        assert error is not None
        assert "0以上で入力してください" in error

    def test_validate_numeric_input_above_maximum(self):
        """Test numeric input validation above maximum."""
        error = self.ui_manager.validate_numeric_input(
            value=200000,
            field_name="テスト金額",
            min_value=0,
            max_value=100000
        )

        assert error is not None
        assert "100,000以下で入力してください" in error

    def test_validate_required_fields_valid(self):
        """Test required fields validation with valid data."""
        errors = self.ui_manager.validate_required_fields(
            store_name="テスト店舗",
            machine_name="テスト機種",
            investment=10000
        )

        assert errors == {}

    def test_validate_required_fields_missing_string(self):
        """Test required fields validation with missing string field."""
        errors = self.ui_manager.validate_required_fields(
            store_name="",
            machine_name="テスト機種",
            investment=10000
        )

        assert "store_name" in errors

    def test_validate_required_fields_missing_numeric(self):
        """Test required fields validation with missing numeric field."""
        errors = self.ui_manager.validate_required_fields(
            store_name="テスト店舗",
            machine_name="テスト機種",
            investment=None
        )

        assert "investment" in errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
