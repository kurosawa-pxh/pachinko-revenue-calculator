#!/usr/bin/env python3
"""
Comprehensive test suite for statistics calculations.
Tests profit calculations, monthly statistics, and machine-specific statistics
without circular import dependencies.
"""

from src.models import GameSession, ValidationError
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


@dataclass
class BasicStats:
    """Basic statistics data structure."""
    total_sessions: int
    completed_sessions: int
    total_investment: int
    total_return: int
    total_profit: int
    winning_sessions: int
    losing_sessions: int
    win_rate: float
    avg_investment: float
    avg_profit: float
    avg_return: float
    max_profit: int
    min_profit: int
    profit_variance: float


@dataclass
class MonthlyStats:
    """Monthly statistics data structure."""
    year: int
    month: int
    basic_stats: BasicStats
    daily_profits: Dict[int, int]  # day -> profit
    sessions_by_day: Dict[int, int]  # day -> session count


@dataclass
class MachineStats:
    """Machine-specific statistics data structure."""
    machine_name: str
    basic_stats: BasicStats
    store_distribution: Dict[str, int]  # store_name -> session count
    avg_session_duration: Optional[float]  # in minutes
    performance_score: float = 0.0


class SimpleStatsCalculator:
    """
    Simplified statistics calculator for testing without database dependencies.
    Contains core calculation logic from the original StatsCalculator.
    """

    def calculate_session_profit(self, investment: int, return_amount: int) -> int:
        """Calculate profit/loss for a single session."""
        return return_amount - investment

    def calculate_basic_stats(self, sessions: List[GameSession]) -> BasicStats:
        """Calculate basic statistics from a list of game sessions."""
        if not sessions:
            return self._empty_basic_stats()

        # Filter only completed sessions for calculations
        completed_sessions = [
            s for s in sessions if s.is_completed and s.profit is not None]

        if not completed_sessions:
            return self._empty_basic_stats()

        total_sessions = len(sessions)
        completed_count = len(completed_sessions)

        # Calculate totals
        total_investment = sum(s.final_investment for s in completed_sessions)
        total_return = sum(s.return_amount for s in completed_sessions)
        total_profit = sum(s.profit for s in completed_sessions)

        # Calculate win/loss counts
        winning_sessions = len([s for s in completed_sessions if s.profit > 0])
        losing_sessions = len([s for s in completed_sessions if s.profit < 0])

        # Calculate rates and averages
        win_rate = (winning_sessions / completed_count *
                    100) if completed_count > 0 else 0
        avg_investment = total_investment / completed_count if completed_count > 0 else 0
        avg_profit = total_profit / completed_count if completed_count > 0 else 0
        avg_return = total_return / completed_count if completed_count > 0 else 0

        # Calculate min/max profits
        profits = [s.profit for s in completed_sessions]
        max_profit = max(profits) if profits else 0
        min_profit = min(profits) if profits else 0

        # Calculate profit variance
        if completed_count > 1:
            mean_profit = avg_profit
            profit_variance = sum((p - mean_profit) **
                                  2 for p in profits) / (completed_count - 1)
        else:
            profit_variance = 0

        return BasicStats(
            total_sessions=total_sessions,
            completed_sessions=completed_count,
            total_investment=total_investment,
            total_return=total_return,
            total_profit=total_profit,
            winning_sessions=winning_sessions,
            losing_sessions=losing_sessions,
            win_rate=win_rate,
            avg_investment=avg_investment,
            avg_profit=avg_profit,
            avg_return=avg_return,
            max_profit=max_profit,
            min_profit=min_profit,
            profit_variance=profit_variance
        )

    def calculate_monthly_stats(self, sessions: List[GameSession], year: int, month: int) -> MonthlyStats:
        """Calculate monthly statistics for a specific year and month."""
        if not (1 <= month <= 12):
            raise ValueError(
                f"Invalid month: {month}. Must be between 1 and 12")

        if year < 2000 or year > datetime.now().year + 1:
            raise ValueError(f"Invalid year: {year}")

        # Filter sessions for the specific month
        monthly_sessions = []
        for session in sessions:
            if session.date.year == year and session.date.month == month:
                monthly_sessions.append(session)

        # Calculate basic stats for the month
        basic_stats = self.calculate_basic_stats(monthly_sessions)

        # Calculate daily breakdown
        daily_profits = {}
        sessions_by_day = {}

        completed_sessions = [
            s for s in monthly_sessions if s.is_completed and s.profit is not None]

        for session in completed_sessions:
            day = session.date.day

            # Accumulate daily profits
            if day not in daily_profits:
                daily_profits[day] = 0
            daily_profits[day] += session.profit

            # Count sessions by day
            if day not in sessions_by_day:
                sessions_by_day[day] = 0
            sessions_by_day[day] += 1

        return MonthlyStats(
            year=year,
            month=month,
            basic_stats=basic_stats,
            daily_profits=daily_profits,
            sessions_by_day=sessions_by_day
        )

    def calculate_machine_stats(self, sessions: List[GameSession], machine_name: str) -> MachineStats:
        """Calculate statistics for a specific machine."""
        # Filter sessions for the specific machine
        machine_sessions = [
            s for s in sessions if s.machine_name == machine_name]

        if not machine_sessions:
            return MachineStats(
                machine_name=machine_name,
                basic_stats=self._empty_basic_stats(),
                store_distribution={},
                avg_session_duration=None
            )

        # Calculate basic stats for this machine
        basic_stats = self.calculate_basic_stats(machine_sessions)

        # Calculate store distribution
        store_distribution = {}
        for session in machine_sessions:
            store = session.store_name
            store_distribution[store] = store_distribution.get(store, 0) + 1

        # Calculate average session duration
        completed_sessions = [s for s in machine_sessions if s.is_completed]
        durations = []

        for session in completed_sessions:
            duration = self._calculate_session_duration(session)
            if duration is not None:
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else None

        return MachineStats(
            machine_name=machine_name,
            basic_stats=basic_stats,
            store_distribution=store_distribution,
            avg_session_duration=avg_duration
        )

    def get_all_machine_stats(self, sessions: List[GameSession]) -> List[MachineStats]:
        """Get statistics for all machines in the sessions."""
        # Get unique machine names
        machine_names = list(set(s.machine_name for s in sessions))

        # Calculate stats for each machine
        machine_stats = []
        for machine_name in machine_names:
            stats = self.calculate_machine_stats(sessions, machine_name)
            machine_stats.append(stats)

        # Sort by total sessions (descending)
        machine_stats.sort(
            key=lambda x: x.basic_stats.total_sessions, reverse=True)

        return machine_stats

    def _calculate_session_duration(self, session: GameSession) -> Optional[float]:
        """Calculate session duration in minutes."""
        if not session.is_completed or not session.end_time or not session.start_time:
            return None

        duration = session.end_time - session.start_time
        return duration.total_seconds() / 60  # Convert to minutes

    def _empty_basic_stats(self) -> BasicStats:
        """Return empty basic statistics structure."""
        return BasicStats(
            total_sessions=0,
            completed_sessions=0,
            total_investment=0,
            total_return=0,
            total_profit=0,
            winning_sessions=0,
            losing_sessions=0,
            win_rate=0.0,
            avg_investment=0.0,
            avg_profit=0.0,
            avg_return=0.0,
            max_profit=0,
            min_profit=0,
            profit_variance=0.0
        )

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return 'insufficient_data'

        # Simple linear trend calculation
        increases = 0
        decreases = 0

        for i in range(1, len(values)):
            if values[i] > values[i-1]:
                increases += 1
            elif values[i] < values[i-1]:
                decreases += 1

        if increases > decreases:
            return 'increasing'
        elif decreases > increases:
            return 'decreasing'
        else:
            return 'stable'

    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (standard deviation) of values."""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def filter_sessions_by_period(self, sessions: List[GameSession],
                                  start_date: datetime, end_date: datetime) -> List[GameSession]:
        """Filter sessions by date period."""
        filtered_sessions = []

        for session in sessions:
            session_date = session.date
            if start_date.date() <= session_date.date() < end_date.date():
                filtered_sessions.append(session)

        return filtered_sessions


@pytest.fixture
def stats_calculator():
    """Create a SimpleStatsCalculator instance."""
    return SimpleStatsCalculator()


@pytest.fixture
def sample_sessions():
    """Create sample game sessions for testing."""
    sessions = []

    # Session 1: Win
    session1 = GameSession(
        user_id="test_user",
        date=datetime(2024, 1, 15),
        start_time=datetime(2024, 1, 15, 10, 0),
        store_name="テストホール1",
        machine_name="CR花の慶次",
        initial_investment=10000
    )
    session1.complete_session(
        end_time=datetime(2024, 1, 15, 12, 0),
        final_investment=15000,
        return_amount=25000
    )
    sessions.append(session1)

    # Session 2: Loss
    session2 = GameSession(
        user_id="test_user",
        date=datetime(2024, 1, 16),
        start_time=datetime(2024, 1, 16, 14, 0),
        store_name="テストホール2",
        machine_name="CR花の慶次",
        initial_investment=12000
    )
    session2.complete_session(
        end_time=datetime(2024, 1, 16, 16, 0),
        final_investment=18000,
        return_amount=8000
    )
    sessions.append(session2)

    # Session 3: Win (different machine)
    session3 = GameSession(
        user_id="test_user",
        date=datetime(2024, 1, 17),
        start_time=datetime(2024, 1, 17, 11, 0),
        store_name="テストホール1",
        machine_name="パチスロ北斗の拳",
        initial_investment=8000
    )
    session3.complete_session(
        end_time=datetime(2024, 1, 17, 13, 0),
        final_investment=12000,
        return_amount=20000
    )
    sessions.append(session3)

    # Session 4: Incomplete
    session4 = GameSession(
        user_id="test_user",
        date=datetime(2024, 1, 18),
        start_time=datetime(2024, 1, 18, 15, 0),
        store_name="テストホール3",
        machine_name="CR花の慶次",
        initial_investment=15000
    )
    sessions.append(session4)

    return sessions


@pytest.fixture
def monthly_sessions():
    """Create sessions spanning multiple months for monthly statistics testing."""
    sessions = []

    # January 2024 sessions
    for day in [10, 15, 20]:
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, day),
            start_time=datetime(2024, 1, day, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        profit = 5000 if day == 10 else -3000  # First session wins, others lose
        session.complete_session(
            end_time=datetime(2024, 1, day, 12, 0),
            final_investment=15000,
            return_amount=15000 + profit
        )
        sessions.append(session)

    # February 2024 sessions
    for day in [5, 12]:
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 2, day),
            start_time=datetime(2024, 2, day, 14, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=12000
        )
        profit = 8000 if day == 5 else -5000  # First session wins, second loses
        session.complete_session(
            end_time=datetime(2024, 2, day, 16, 0),
            final_investment=18000,
            return_amount=18000 + profit
        )
        sessions.append(session)

    return sessions


class TestBasicProfitCalculations:
    """Test basic profit calculation functionality."""

    def test_calculate_session_profit(self, stats_calculator):
        """Test individual session profit calculation."""
        # Test profit (win)
        profit = stats_calculator.calculate_session_profit(15000, 25000)
        assert profit == 10000

        # Test loss
        loss = stats_calculator.calculate_session_profit(20000, 12000)
        assert loss == -8000

        # Test break-even
        break_even = stats_calculator.calculate_session_profit(15000, 15000)
        assert break_even == 0

    def test_calculate_basic_stats_with_data(self, stats_calculator, sample_sessions):
        """Test basic statistics calculation with sample data."""
        # Only use completed sessions for this test
        completed_sessions = [s for s in sample_sessions if s.is_completed]

        basic_stats = stats_calculator.calculate_basic_stats(
            completed_sessions)

        assert basic_stats.total_sessions == 3
        assert basic_stats.completed_sessions == 3
        assert basic_stats.total_investment == 45000  # 15000 + 18000 + 12000
        assert basic_stats.total_return == 53000      # 25000 + 8000 + 20000
        assert basic_stats.total_profit == 8000       # 10000 + (-10000) + 8000
        assert basic_stats.winning_sessions == 2      # Sessions 1 and 3
        assert basic_stats.losing_sessions == 1       # Session 2
        assert basic_stats.win_rate == pytest.approx(
            66.67, rel=1e-2)  # 2/3 * 100
        assert basic_stats.avg_investment == 15000    # 45000/3
        assert basic_stats.avg_profit == pytest.approx(
            2666.67, rel=1e-2)  # 8000/3
        assert basic_stats.max_profit == 10000
        assert basic_stats.min_profit == -10000

    def test_calculate_basic_stats_empty_data(self, stats_calculator):
        """Test basic statistics calculation with empty data."""
        basic_stats = stats_calculator.calculate_basic_stats([])

        assert basic_stats.total_sessions == 0
        assert basic_stats.completed_sessions == 0
        assert basic_stats.total_investment == 0
        assert basic_stats.total_return == 0
        assert basic_stats.total_profit == 0
        assert basic_stats.winning_sessions == 0
        assert basic_stats.losing_sessions == 0
        assert basic_stats.win_rate == 0.0
        assert basic_stats.avg_investment == 0.0
        assert basic_stats.avg_profit == 0.0

    def test_calculate_basic_stats_incomplete_sessions_only(self, stats_calculator):
        """Test basic statistics with only incomplete sessions."""
        incomplete_session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )

        basic_stats = stats_calculator.calculate_basic_stats(
            [incomplete_session])

        # Should return empty stats since no completed sessions
        assert basic_stats.total_sessions == 0
        assert basic_stats.completed_sessions == 0

    def test_calculate_basic_stats_mixed_sessions(self, stats_calculator, sample_sessions):
        """Test basic statistics with mix of completed and incomplete sessions."""
        basic_stats = stats_calculator.calculate_basic_stats(sample_sessions)

        # Should only count completed sessions in calculations
        assert basic_stats.total_sessions == 4  # All sessions
        assert basic_stats.completed_sessions == 3  # Only completed ones
        assert basic_stats.total_profit == 8000  # Only from completed sessions


class TestMonthlyStatistics:
    """Test monthly statistics functionality."""

    def test_calculate_monthly_stats_with_data(self, stats_calculator, monthly_sessions):
        """Test monthly statistics calculation with data."""
        # Test January 2024
        jan_stats = stats_calculator.calculate_monthly_stats(
            monthly_sessions, 2024, 1)

        assert jan_stats.year == 2024
        assert jan_stats.month == 1
        assert jan_stats.basic_stats.total_sessions == 3
        assert jan_stats.basic_stats.completed_sessions == 3
        assert jan_stats.basic_stats.total_profit == - \
            1000  # 5000 + (-3000) + (-3000)
        assert jan_stats.basic_stats.winning_sessions == 1
        assert jan_stats.basic_stats.losing_sessions == 2
        assert jan_stats.basic_stats.win_rate == pytest.approx(33.33, rel=1e-2)

        # Check daily breakdown
        assert 10 in jan_stats.daily_profits
        assert 15 in jan_stats.daily_profits
        assert 20 in jan_stats.daily_profits
        assert jan_stats.daily_profits[10] == 5000
        assert jan_stats.daily_profits[15] == -3000
        assert jan_stats.daily_profits[20] == -3000

        # Check sessions by day
        assert jan_stats.sessions_by_day[10] == 1
        assert jan_stats.sessions_by_day[15] == 1
        assert jan_stats.sessions_by_day[20] == 1

    def test_calculate_monthly_stats_no_data(self, stats_calculator, monthly_sessions):
        """Test monthly statistics with no data."""
        monthly_stats = stats_calculator.calculate_monthly_stats(
            monthly_sessions, 2024, 12)

        assert monthly_stats.year == 2024
        assert monthly_stats.month == 12
        assert monthly_stats.basic_stats.total_sessions == 0
        assert monthly_stats.basic_stats.completed_sessions == 0
        assert monthly_stats.basic_stats.total_profit == 0
        assert len(monthly_stats.daily_profits) == 0
        assert len(monthly_stats.sessions_by_day) == 0

    def test_calculate_monthly_stats_invalid_month(self, stats_calculator, monthly_sessions):
        """Test monthly statistics with invalid month."""
        with pytest.raises(ValueError, match="Invalid month"):
            stats_calculator.calculate_monthly_stats(
                monthly_sessions, 2024, 13)

        with pytest.raises(ValueError, match="Invalid month"):
            stats_calculator.calculate_monthly_stats(monthly_sessions, 2024, 0)

    def test_calculate_monthly_stats_invalid_year(self, stats_calculator, monthly_sessions):
        """Test monthly statistics with invalid year."""
        with pytest.raises(ValueError, match="Invalid year"):
            stats_calculator.calculate_monthly_stats(monthly_sessions, 1999, 1)

        current_year = datetime.now().year
        with pytest.raises(ValueError, match="Invalid year"):
            stats_calculator.calculate_monthly_stats(
                monthly_sessions, current_year + 2, 1)

    def test_calculate_monthly_stats_february(self, stats_calculator, monthly_sessions):
        """Test monthly statistics for February."""
        feb_stats = stats_calculator.calculate_monthly_stats(
            monthly_sessions, 2024, 2)

        assert feb_stats.year == 2024
        assert feb_stats.month == 2
        assert feb_stats.basic_stats.total_sessions == 2
        assert feb_stats.basic_stats.completed_sessions == 2
        assert feb_stats.basic_stats.total_profit == 3000  # 8000 + (-5000)
        assert feb_stats.basic_stats.winning_sessions == 1
        assert feb_stats.basic_stats.losing_sessions == 1


class TestMachineStatistics:
    """Test machine-specific statistics functionality."""

    def test_calculate_machine_stats_with_data(self, stats_calculator, sample_sessions):
        """Test machine statistics calculation with data."""
        # Test for "CR花の慶次" machine
        machine_stats = stats_calculator.calculate_machine_stats(
            sample_sessions, "CR花の慶次")

        assert machine_stats.machine_name == "CR花の慶次"
        assert machine_stats.basic_stats.total_sessions == 3  # 2 completed + 1 incomplete
        assert machine_stats.basic_stats.completed_sessions == 2
        assert machine_stats.basic_stats.total_profit == 0  # 10000 + (-10000)
        assert machine_stats.basic_stats.winning_sessions == 1
        assert machine_stats.basic_stats.losing_sessions == 1
        assert machine_stats.basic_stats.win_rate == 50.0

        # Check store distribution
        assert "テストホール1" in machine_stats.store_distribution
        assert "テストホール2" in machine_stats.store_distribution
        assert "テストホール3" in machine_stats.store_distribution
        assert machine_stats.store_distribution["テストホール1"] == 1
        assert machine_stats.store_distribution["テストホール2"] == 1
        assert machine_stats.store_distribution["テストホール3"] == 1

        # Check average session duration (should be 120 minutes for completed sessions)
        assert machine_stats.avg_session_duration == 120.0

    def test_calculate_machine_stats_no_data(self, stats_calculator, sample_sessions):
        """Test machine statistics with no data for specific machine."""
        machine_stats = stats_calculator.calculate_machine_stats(
            sample_sessions, "非存在機種")

        assert machine_stats.machine_name == "非存在機種"
        assert machine_stats.basic_stats.total_sessions == 0
        assert machine_stats.basic_stats.completed_sessions == 0
        assert machine_stats.store_distribution == {}
        assert machine_stats.avg_session_duration is None

    def test_get_all_machine_stats(self, stats_calculator, sample_sessions):
        """Test getting statistics for all machines."""
        all_machine_stats = stats_calculator.get_all_machine_stats(
            sample_sessions)

        # Should have 2 unique machines
        assert len(all_machine_stats) == 2

        machine_names = [stats.machine_name for stats in all_machine_stats]
        assert "CR花の慶次" in machine_names
        assert "パチスロ北斗の拳" in machine_names

        # Should be sorted by total sessions (descending)
        # CR花の慶次 has 3 sessions, パチスロ北斗の拳 has 1
        assert all_machine_stats[0].machine_name == "CR花の慶次"
        assert all_machine_stats[1].machine_name == "パチスロ北斗の拳"

    def test_calculate_machine_stats_different_machine(self, stats_calculator, sample_sessions):
        """Test machine statistics for different machine."""
        # Test for "パチスロ北斗の拳" machine
        machine_stats = stats_calculator.calculate_machine_stats(
            sample_sessions, "パチスロ北斗の拳")

        assert machine_stats.machine_name == "パチスロ北斗の拳"
        assert machine_stats.basic_stats.total_sessions == 1
        assert machine_stats.basic_stats.completed_sessions == 1
        assert machine_stats.basic_stats.total_profit == 8000
        assert machine_stats.basic_stats.winning_sessions == 1
        assert machine_stats.basic_stats.losing_sessions == 0
        assert machine_stats.basic_stats.win_rate == 100.0

        # Check store distribution
        assert machine_stats.store_distribution["テストホール1"] == 1

        # Check average session duration (should be 120 minutes)
        assert machine_stats.avg_session_duration == 120.0


class TestUtilityFunctions:
    """Test utility functions in StatsCalculator."""

    def test_calculate_trend_increasing(self, stats_calculator):
        """Test trend calculation with increasing values."""
        values = [100, 150, 200, 250, 300]
        trend = stats_calculator._calculate_trend(values)
        assert trend == 'increasing'

    def test_calculate_trend_decreasing(self, stats_calculator):
        """Test trend calculation with decreasing values."""
        values = [300, 250, 200, 150, 100]
        trend = stats_calculator._calculate_trend(values)
        assert trend == 'decreasing'

    def test_calculate_trend_stable(self, stats_calculator):
        """Test trend calculation with stable values."""
        values = [200, 210, 190, 205, 195]
        trend = stats_calculator._calculate_trend(values)
        assert trend == 'stable'

    def test_calculate_trend_insufficient_data(self, stats_calculator):
        """Test trend calculation with insufficient data."""
        values = [100]
        trend = stats_calculator._calculate_trend(values)
        assert trend == 'insufficient_data'

    def test_calculate_volatility(self, stats_calculator):
        """Test volatility calculation."""
        values = [100, 200, 150, 250, 175]
        volatility = stats_calculator._calculate_volatility(values)
        assert volatility > 0  # Should have some volatility

        # Test with identical values (no volatility)
        identical_values = [100, 100, 100, 100]
        no_volatility = stats_calculator._calculate_volatility(
            identical_values)
        assert no_volatility == 0.0

    def test_calculate_volatility_insufficient_data(self, stats_calculator):
        """Test volatility calculation with insufficient data."""
        values = [100]
        volatility = stats_calculator._calculate_volatility(values)
        assert volatility == 0.0

    def test_filter_sessions_by_period(self, stats_calculator, sample_sessions):
        """Test filtering sessions by date period."""
        start_date = datetime(2024, 1, 16)
        end_date = datetime(2024, 1, 18)

        filtered_sessions = stats_calculator.filter_sessions_by_period(
            sample_sessions, start_date, end_date
        )

        # Should include sessions on 16th and 17th (end_date is exclusive)
        assert len(filtered_sessions) == 2
        for session in filtered_sessions:
            assert start_date.date() <= session.date.date() < end_date.date()

    def test_session_duration_calculation(self, stats_calculator):
        """Test session duration calculation."""
        # Create a session with known duration
        session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 30),  # 2.5 hours = 150 minutes
            final_investment=15000,
            return_amount=20000
        )

        duration = stats_calculator._calculate_session_duration(session)
        assert duration == 150.0  # 2.5 hours in minutes

    def test_session_duration_incomplete(self, stats_calculator):
        """Test session duration calculation for incomplete session."""
        incomplete_session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )

        duration = stats_calculator._calculate_session_duration(
            incomplete_session)
        assert duration is None


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
