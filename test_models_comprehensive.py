#!/usr/bin/env python3
"""
Comprehensive test suite for GameSession model.
Tests validation functionality, session completion, and dictionary conversion.
"""

from src.models import GameSession, ValidationError
import pytest
from datetime import datetime, timedelta
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


class TestGameSessionValidation:
    """Test GameSession validation functionality."""

    def test_valid_session_creation(self):
        """Test creating a valid GameSession."""
        session = GameSession(
            user_id="test_user_123",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="パチンコホール太郎",
            machine_name="CR花の慶次",
            initial_investment=10000
        )

        assert session.user_id == "test_user_123"
        assert session.store_name == "パチンコホール太郎"
        assert session.machine_name == "CR花の慶次"
        assert session.initial_investment == 10000
        assert session.is_completed is False
        assert session.profit is None

    def test_user_id_validation(self):
        """Test user_id validation rules."""
        # Empty user_id should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
        assert "ユーザーIDは必須です" in str(exc_info.value)

        # Whitespace-only user_id should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="   ",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
        assert "ユーザーIDは必須です" in str(exc_info.value)

    def test_store_name_validation(self):
        """Test store_name validation rules."""
        # Empty store_name should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
        assert "店舗名は必須です" in str(exc_info.value)

        # Valid Japanese store names should pass
        valid_names = [
            "パチンコホール太郎",
            "マルハン新宿店",
            "ガイア123",
            "P-WORLD東京"
        ]
        for name in valid_names:
            session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name=name,
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            assert session.store_name == name

    def test_machine_name_validation(self):
        """Test machine_name validation rules."""
        # Empty machine_name should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="",
                initial_investment=10000
            )
        assert "機種名は必須です" in str(exc_info.value)

        # Valid machine names should pass
        valid_names = [
            "CR花の慶次",
            "パチスロ北斗の拳",
            "CRフィーバー戦姫絶唱シンフォギア",
            "P真・北斗無双(第3章)"
        ]
        for name in valid_names:
            session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name=name,
                initial_investment=10000
            )
            assert session.machine_name == name

    def test_initial_investment_validation(self):
        """Test initial_investment validation rules."""
        # None should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=None
            )
        assert "開始投資額は必須です" in str(exc_info.value)

        # Negative amount should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=-1000
            )
        assert "開始投資額は0以上で入力してください" in str(exc_info.value)

        # Amount over limit should fail
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=1000001
            )
        assert "開始投資額は100万円以下で入力してください" in str(exc_info.value)

        # Valid amounts should pass
        valid_amounts = [0, 1000, 10000, 50000, 100000, 1000000]
        for amount in valid_amounts:
            session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=amount
            )
            assert session.initial_investment == amount

    def test_date_validation(self):
        """Test date validation rules."""
        # Future date should fail
        future_date = datetime.now() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc_info:
            GameSession(
                user_id="test_user",
                date=future_date,
                start_time=future_date,
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
        assert "未来の日付は入力できません" in str(exc_info.value)

        # Today's date should pass
        today = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        session = GameSession(
            user_id="test_user",
            date=today,
            start_time=today,
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        assert session.date.date() == today.date()


class TestGameSessionCompletion:
    """Test GameSession completion functionality."""

    def create_test_session(self):
        """Helper method to create a test session."""
        return GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )

    def test_successful_session_completion(self):
        """Test successful session completion."""
        session = self.create_test_session()

        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )

        assert session.is_completed is True
        assert session.end_time == datetime(2024, 1, 15, 12, 0)
        assert session.final_investment == 15000
        assert session.return_amount == 20000
        assert session.profit == 5000  # 20000 - 15000

    def test_session_completion_with_loss(self):
        """Test session completion with loss."""
        session = self.create_test_session()

        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=8000
        )

        assert session.is_completed is True
        assert session.profit == -7000  # 8000 - 15000

    def test_invalid_end_time(self):
        """Test completion with invalid end time."""
        session = self.create_test_session()

        # End time before start time should fail
        with pytest.raises(ValidationError) as exc_info:
            session.complete_session(
                end_time=datetime(2024, 1, 15, 9, 0),  # Before start time
                final_investment=15000,
                return_amount=20000
            )
        assert "終了時間は開始時間より後である必要があります" in str(exc_info.value)

    def test_invalid_final_investment(self):
        """Test completion with invalid final investment."""
        session = self.create_test_session()

        # Final investment less than initial should fail
        with pytest.raises(ValidationError) as exc_info:
            session.complete_session(
                end_time=datetime(2024, 1, 15, 12, 0),
                final_investment=5000,  # Less than initial 10000
                return_amount=20000
            )
        assert "最終投資額は開始投資額以上である必要があります" in str(exc_info.value)

        # Negative final investment should fail
        with pytest.raises(ValidationError) as exc_info:
            session.complete_session(
                end_time=datetime(2024, 1, 15, 12, 0),
                final_investment=-1000,
                return_amount=20000
            )
        assert "最終投資額は0以上で入力してください" in str(exc_info.value)

    def test_invalid_return_amount(self):
        """Test completion with invalid return amount."""
        session = self.create_test_session()

        # Negative return amount should fail
        with pytest.raises(ValidationError) as exc_info:
            session.complete_session(
                end_time=datetime(2024, 1, 15, 12, 0),
                final_investment=15000,
                return_amount=-1000
            )
        assert "回収金額は0以上で入力してください" in str(exc_info.value)

        # Return amount over limit should fail
        with pytest.raises(ValidationError) as exc_info:
            session.complete_session(
                end_time=datetime(2024, 1, 15, 12, 0),
                final_investment=15000,
                return_amount=10000001
            )
        assert "回収金額は1000万円以下で入力してください" in str(exc_info.value)

    def test_calculate_profit_incomplete_session(self):
        """Test profit calculation for incomplete session."""
        session = self.create_test_session()

        # Incomplete session should return None for profit
        profit = session.calculate_profit()
        assert profit is None
        assert session.profit is None

    def test_calculate_profit_completed_session(self):
        """Test profit calculation for completed session."""
        session = self.create_test_session()
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )

        profit = session.calculate_profit()
        assert profit == 5000
        assert session.profit == 5000


class TestGameSessionDictConversion:
    """Test GameSession dictionary conversion functionality."""

    def create_completed_session(self):
        """Helper method to create a completed test session."""
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=15000,
            return_amount=20000
        )
        return session

    def test_to_dict_incomplete_session(self):
        """Test converting incomplete session to dictionary."""
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )

        session_dict = session.to_dict()

        assert session_dict['user_id'] == "test_user"
        assert session_dict['store_name'] == "テストホール"
        assert session_dict['machine_name'] == "CR花の慶次"
        assert session_dict['initial_investment'] == 10000
        assert session_dict['is_completed'] is False
        assert session_dict['final_investment'] is None
        assert session_dict['return_amount'] is None
        assert session_dict['profit'] is None
        assert session_dict['end_time'] is None

    def test_to_dict_completed_session(self):
        """Test converting completed session to dictionary."""
        session = self.create_completed_session()
        session_dict = session.to_dict()

        assert session_dict['user_id'] == "test_user"
        assert session_dict['store_name'] == "テストホール"
        assert session_dict['machine_name'] == "CR花の慶次"
        assert session_dict['initial_investment'] == 10000
        assert session_dict['final_investment'] == 15000
        assert session_dict['return_amount'] == 20000
        assert session_dict['profit'] == 5000
        assert session_dict['is_completed'] is True

        # Check datetime fields are properly converted to ISO format
        assert isinstance(session_dict['date'], str)
        assert isinstance(session_dict['start_time'], str)
        assert isinstance(session_dict['end_time'], str)
        assert isinstance(session_dict['created_at'], str)
        assert isinstance(session_dict['updated_at'], str)

    def test_from_dict_incomplete_session(self):
        """Test creating session from dictionary (incomplete)."""
        session_data = {
            'id': 1,
            'user_id': 'test_user',
            'date': '2024-01-15T00:00:00',
            'start_time': '2024-01-15T10:00:00',
            'end_time': None,
            'store_name': 'テストホール',
            'machine_name': 'CR花の慶次',
            'initial_investment': 10000,
            'final_investment': None,
            'return_amount': None,
            'profit': None,
            'is_completed': False,
            'created_at': '2024-01-15T10:00:00',
            'updated_at': '2024-01-15T10:00:00'
        }

        session = GameSession.from_dict(session_data)

        assert session.id == 1
        assert session.user_id == 'test_user'
        assert session.store_name == 'テストホール'
        assert session.machine_name == 'CR花の慶次'
        assert session.initial_investment == 10000
        assert session.is_completed is False
        assert session.final_investment is None
        assert session.return_amount is None
        assert session.profit is None

    def test_from_dict_completed_session(self):
        """Test creating session from dictionary (completed)."""
        session_data = {
            'id': 1,
            'user_id': 'test_user',
            'date': '2024-01-15T00:00:00',
            'start_time': '2024-01-15T10:00:00',
            'end_time': '2024-01-15T12:00:00',
            'store_name': 'テストホール',
            'machine_name': 'CR花の慶次',
            'initial_investment': 10000,
            'final_investment': 15000,
            'return_amount': 20000,
            'profit': 5000,
            'is_completed': True,
            'created_at': '2024-01-15T10:00:00',
            'updated_at': '2024-01-15T12:00:00'
        }

        session = GameSession.from_dict(session_data)

        assert session.id == 1
        assert session.user_id == 'test_user'
        assert session.store_name == 'テストホール'
        assert session.machine_name == 'CR花の慶次'
        assert session.initial_investment == 10000
        assert session.final_investment == 15000
        assert session.return_amount == 20000
        assert session.profit == 5000
        assert session.is_completed is True

    def test_round_trip_conversion(self):
        """Test converting to dict and back maintains data integrity."""
        original_session = self.create_completed_session()

        # Convert to dict and back
        session_dict = original_session.to_dict()
        restored_session = GameSession.from_dict(session_dict)

        # Check all important fields are preserved
        assert original_session.user_id == restored_session.user_id
        assert original_session.store_name == restored_session.store_name
        assert original_session.machine_name == restored_session.machine_name
        assert original_session.initial_investment == restored_session.initial_investment
        assert original_session.final_investment == restored_session.final_investment
        assert original_session.return_amount == restored_session.return_amount
        assert original_session.profit == restored_session.profit
        assert original_session.is_completed == restored_session.is_completed

        # Check datetime fields (comparing dates since microseconds might differ)
        assert original_session.date.date() == restored_session.date.date()
        assert original_session.start_time.replace(
            microsecond=0) == restored_session.start_time.replace(microsecond=0)
        assert original_session.end_time.replace(
            microsecond=0) == restored_session.end_time.replace(microsecond=0)

    def test_from_dict_missing_optional_fields(self):
        """Test creating session from dict with missing optional fields."""
        minimal_data = {
            'user_id': 'test_user',
            'date': '2024-01-15T00:00:00',
            'start_time': '2024-01-15T10:00:00',
            'store_name': 'テストホール',
            'machine_name': 'CR花の慶次',
            'initial_investment': 10000
        }

        session = GameSession.from_dict(minimal_data)

        assert session.user_id == 'test_user'
        assert session.store_name == 'テストホール'
        assert session.machine_name == 'CR花の慶次'
        assert session.initial_investment == 10000
        assert session.is_completed is False
        assert session.id is None
        assert session.final_investment is None
        assert session.return_amount is None
        assert session.profit is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
