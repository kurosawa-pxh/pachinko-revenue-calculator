"""
Data models for the Pachinko Revenue Calculator application.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
import re


# ValidationError moved to exceptions.py to avoid circular imports
from .exceptions import ValidationError


@dataclass
class GameSession:
    """
    Data model for a pachinko game session.

    Represents a single gaming session with start/end data and calculated profit.
    Includes validation for all required fields and business logic constraints.
    """
    # Required fields for session start (no defaults)
    user_id: str
    date: date
    start_time: datetime
    store_name: str
    machine_name: str
    initial_investment: int

    # Optional fields (set during session end)
    id: Optional[int] = None
    end_time: Optional[datetime] = None
    final_investment: Optional[int] = None
    return_amount: Optional[int] = None
    profit: Optional[int] = None
    is_completed: bool = False

    # Metadata fields
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization processing to ensure data types."""
        # Ensure user_id is always a string
        if self.user_id is not None:
            self.user_id = str(self.user_id)

    def __post_init__(self):
        """Validate the data after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate all fields according to business rules.

        Raises:
            ValidationError: If any validation rule is violated.
        """
        # Validate required string fields
        if not self.user_id or not str(self.user_id).strip():
            raise ValidationError("user_id", "ユーザーIDは必須です")

        if not self.store_name or not self.store_name.strip():
            raise ValidationError("store_name", "店舗名は必須です")

        if not self.machine_name or not self.machine_name.strip():
            raise ValidationError("machine_name", "機種名は必須です")

        # Validate store name format (Japanese characters, alphanumeric, and common symbols)
        if not re.match(r'^[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\s\-_]+$', self.store_name):
            raise ValidationError("store_name", "店舗名に無効な文字が含まれています")

        # Validate machine name format (Japanese characters, alphanumeric, and common symbols)
        if not re.match(r'^[a-zA-Z0-9\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\s\-_()]+$', self.machine_name):
            raise ValidationError("machine_name", "機種名に無効な文字が含まれています")

        # Validate initial investment
        if self.initial_investment is None:
            raise ValidationError("initial_investment", "開始投資額は必須です")

        if not isinstance(self.initial_investment, int):
            raise ValidationError("initial_investment", "開始投資額は整数で入力してください")

        if self.initial_investment < 0:
            raise ValidationError("initial_investment", "開始投資額は0以上で入力してください")

        if self.initial_investment > 1000000:  # 100万円上限
            raise ValidationError("initial_investment",
                                  "開始投資額は100万円以下で入力してください")

        # Validate date and time
        if not isinstance(self.date, datetime):
            raise ValidationError("date", "日付の形式が正しくありません")

        if not isinstance(self.start_time, datetime):
            raise ValidationError("start_time", "開始時間の形式が正しくありません")

        # Validate future date constraint
        if self.date.date() > datetime.now().date():
            raise ValidationError("date", "未来の日付は入力できません")

        # Validate completed session fields
        if self.is_completed:
            self._validate_completed_session()

    def _validate_completed_session(self) -> None:
        """Validate fields required for completed sessions."""
        if self.end_time is None:
            raise ValidationError("end_time", "終了時間は必須です")

        if self.final_investment is None:
            raise ValidationError("final_investment", "最終投資額は必須です")

        if self.return_amount is None:
            raise ValidationError("return_amount", "回収金額は必須です")

        # Validate final investment
        if not isinstance(self.final_investment, int):
            raise ValidationError("final_investment", "最終投資額は整数で入力してください")

        if self.final_investment < 0:
            raise ValidationError("final_investment", "最終投資額は0以上で入力してください")

        if self.final_investment > 1000000:  # 100万円上限
            raise ValidationError("final_investment", "最終投資額は100万円以下で入力してください")

        # Validate return amount
        if not isinstance(self.return_amount, int):
            raise ValidationError("return_amount", "回収金額は整数で入力してください")

        if self.return_amount < 0:
            raise ValidationError("return_amount", "回収金額は0以上で入力してください")

        if self.return_amount > 10000000:  # 1000万円上限
            raise ValidationError("return_amount", "回収金額は1000万円以下で入力してください")

        # Validate time sequence
        if self.end_time <= self.start_time:
            raise ValidationError("end_time", "終了時間は開始時間より後である必要があります")

        # Validate logical constraints
        if self.final_investment < self.initial_investment:
            raise ValidationError("final_investment",
                                  "最終投資額は開始投資額以上である必要があります")

    def calculate_profit(self) -> Optional[int]:
        """
        Calculate the profit/loss for this session.

        Returns:
            int: Profit (positive) or loss (negative) amount, or None if session not completed.
        """
        if not self.is_completed or self.final_investment is None or self.return_amount is None:
            return None

        self.profit = self.return_amount - self.final_investment
        return self.profit

    def complete_session(self, end_time: datetime, final_investment: int, return_amount: int) -> None:
        """
        Complete the session with end data and calculate profit.

        Args:
            end_time: When the session ended
            final_investment: Total amount invested
            return_amount: Total amount returned

        Raises:
            ValidationError: If the completion data is invalid
        """
        self.end_time = end_time
        self.final_investment = final_investment
        self.return_amount = return_amount
        self.is_completed = True
        self.updated_at = datetime.now()

        # Validate the completed session
        self._validate_completed_session()

        # Calculate profit
        self.calculate_profit()

    def to_dict(self) -> dict:
        """
        Convert the session to a dictionary for database storage.

        Returns:
            dict: Dictionary representation of the session
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date.isoformat() if self.date else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'store_name': self.store_name,
            'machine_name': self.machine_name,
            'initial_investment': self.initial_investment,
            'final_investment': self.final_investment,
            'return_amount': self.return_amount,
            'profit': self.profit,
            'is_completed': self.is_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameSession':
        """
        Create a GameSession from a dictionary (e.g., from database).

        Args:
            data: Dictionary containing session data

        Returns:
            GameSession: New instance created from the data
        """
        # Convert ISO format strings back to datetime objects
        date = datetime.fromisoformat(
            data['date']) if data.get('date') else None
        start_time = datetime.fromisoformat(
            data['start_time']) if data.get('start_time') else None
        end_time = datetime.fromisoformat(
            data['end_time']) if data.get('end_time') else None
        created_at = datetime.fromisoformat(data['created_at']) if data.get(
            'created_at') else datetime.now()
        updated_at = datetime.fromisoformat(data['updated_at']) if data.get(
            'updated_at') else datetime.now()

        return cls(
            id=data.get('id'),
            user_id=data['user_id'],
            date=date,
            start_time=start_time,
            end_time=end_time,
            store_name=data['store_name'],
            machine_name=data['machine_name'],
            initial_investment=data['initial_investment'],
            final_investment=data.get('final_investment'),
            return_amount=data.get('return_amount'),
            profit=data.get('profit'),
            is_completed=data.get('is_completed', False),
            created_at=created_at,
            updated_at=updated_at
        )

    def __str__(self) -> str:
        """String representation of the session."""
        status = "完了" if self.is_completed else "進行中"
        profit_str = f"収支: {self.profit:+,}円" if self.profit is not None else "収支: 未計算"
        return f"{self.date.strftime('%Y/%m/%d')} {self.store_name} {self.machine_name} ({status}) {profit_str}"
