#!/usr/bin/env python3
"""
Comprehensive test suite for StatsCalculator.
Tests profit calculations, monthly statistics, and machine-specific statistics.
"""

from src.stats import StatsCalculator, BasicStats, MonthlyStats, MachineStats
from src.models import GameSession, ValidationError
import pytest
from datetime import datetime, timedelta
from typing import List
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


class MockDatabaseManager:
    """Mock database manager for testing statistics without database dependencies."""

    def __init__(self):
        self.sessions = []

    def add_session(self, session: GameSession):
        """Add a session to the mock database."""
        if session.id is None:
            session.id = len(self.sessions) + 1
        self.sessions.append(session)

    def get_sessions(self, user_id: str, date_range=None, limit=None, offset=0):
        """Get sessions from mock database."""
        filtered_sessions = [s for s in self.sessions if s.user_id == user_id]

        if date_range:
            start_date, end_date = date_range
            filtered_sessions = [
                s for s in filtered_sessions
                if start_date.date() <= s.date.date() < end_date.date()
            ]

        # Apply pagination
        if offset > 0:
            filtered_sessions = filtered_sessions[offset:]
        if limit:
            filtered_sessions = filtered_sessions[:limit]

        return filtered_sessions


@pytest.fixture
def mock_db():
    """Create a mock database manager."""
    return MockDatabaseManager()


@pytest.fixture
def stats_calculator(mock_db):
    """Create a StatsCalculator with mock database."""
    return StatsCalculator(mock_db)


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

    def setup_monthly_data(self, mock_db, monthly_sessions):
        """Helper to set up monthly test data."""
        for session in monthly_sessions:
            mock_db.add_session(session)

    def test_calculate_monthly_stats_with_data(self, stats_calculator, mock_db, monthly_sessions):
        """Test monthly statistics calculation with data."""
        self.setup_monthly_data(mock_db, monthly_sessions)

        # Test January 2024
        jan_stats = stats_calculator.calculate_monthly_stats(
            "test_user", 2024, 1)

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

    def test_calculate_monthly_stats_no_data(self, stats_calculator, mock_db):
        """Test monthly statistics with no data."""
        monthly_stats = stats_calculator.calculate_monthly_stats(
            "test_user", 2024, 12)

        assert monthly_stats.year == 2024
        assert monthly_stats.month == 12
        assert monthly_stats.basic_stats.total_sessions == 0
        assert monthly_stats.basic_stats.completed_sessions == 0
        assert monthly_stats.basic_stats.total_profit == 0
        assert len(monthly_stats.daily_profits) == 0
        assert len(monthly_stats.sessions_by_day) == 0

    def test_calculate_monthly_stats_invalid_month(self, stats_calculator):
        """Test monthly statistics with invalid month."""
        with pytest.raises(ValueError, match="Invalid month"):
            stats_calculator.calculate_monthly_stats("test_user", 2024, 13)

        with pytest.raises(ValueError, match="Invalid month"):
            stats_calculator.calculate_monthly_stats("test_user", 2024, 0)

    def test_calculate_monthly_stats_invalid_year(self, stats_calculator):
        """Test monthly statistics with invalid year."""
        with pytest.raises(ValueError, match="Invalid year"):
            stats_calculator.calculate_monthly_stats("test_user", 1999, 1)

        current_year = datetime.now().year
        with pytest.raises(ValueError, match="Invalid year"):
            stats_calculator.calculate_monthly_stats(
                "test_user", current_year + 2, 1)

    def test_get_monthly_stats_range(self, stats_calculator, mock_db, monthly_sessions):
        """Test getting monthly statistics for a range of months."""
        self.setup_monthly_data(mock_db, monthly_sessions)

        # Get stats for Jan-Feb 2024
        monthly_range = stats_calculator.get_monthly_stats_range(
            "test_user", 2024, 1, 2024, 2
        )

        assert len(monthly_range) == 2
        assert monthly_range[0].year == 2024 and monthly_range[0].month == 1
        assert monthly_range[1].year == 2024 and monthly_range[1].month == 2

        # Check that data is correct for each month
        jan_stats = monthly_range[0]
        feb_stats = monthly_range[1]

        assert jan_stats.basic_stats.total_sessions == 3
        assert feb_stats.basic_stats.total_sessions == 2

    def test_get_monthly_stats_range_invalid_range(self, stats_calculator):
        """Test monthly stats range with invalid date range."""
        with pytest.raises(ValueError, match="Start date must be before"):
            stats_calculator.get_monthly_stats_range(
                "test_user", 2024, 6, 2024, 3)

    def test_get_monthly_comparison(self, stats_calculator, mock_db, monthly_sessions):
        """Test monthly comparison functionality."""
        self.setup_monthly_data(mock_db, monthly_sessions)

        comparison = stats_calculator.get_monthly_comparison(
            "test_user", [(2024, 1), (2024, 2)]
        )

        assert len(comparison['months_data']) == 2
        assert 'best_month' in comparison
        assert 'worst_month' in comparison
        assert 'profit_trend' in comparison
        assert 'total_profit' in comparison

        # February should be better (3000 total vs -1000)
        assert comparison['best_month']['month'] == 2
        assert comparison['worst_month']['month'] == 1

    def test_get_monthly_comparison_empty_months(self, stats_calculator):
        """Test monthly comparison with empty months list."""
        with pytest.raises(ValueError, match="At least one month must be provided"):
            stats_calculator.get_monthly_comparison("test_user", [])


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

    def test_get_all_machine_stats(self, stats_calculator, mock_db, sample_sessions):
        """Test getting statistics for all machines."""
        for session in sample_sessions:
            mock_db.add_session(session)

        all_machine_stats = stats_calculator.get_all_machine_stats("test_user")

        # Should have 2 unique machines
        assert len(all_machine_stats) == 2

        machine_names = [stats.machine_name for stats in all_machine_stats]
        assert "CR花の慶次" in machine_names
        assert "パチスロ北斗の拳" in machine_names

        # Should be sorted by total sessions (descending)
        # CR花の慶次 has 3 sessions, パチスロ北斗の拳 has 1
        assert all_machine_stats[0].machine_name == "CR花の慶次"
        assert all_machine_stats[1].machine_name == "パチスロ北斗の拳"

    def test_get_machine_performance_ranking(self, stats_calculator, mock_db, sample_sessions):
        """Test machine performance ranking."""
        for session in sample_sessions:
            mock_db.add_session(session)

        # Add more sessions to meet minimum requirements
        additional_sessions = []
        for i in range(3):
            session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 20 + i),
                start_time=datetime(2024, 1, 20 + i, 10, 0),
                store_name="テストホール",
                machine_name="パチスロ北斗の拳",
                initial_investment=10000
            )
            session.complete_session(
                end_time=datetime(2024, 1, 20 + i, 12, 0),
                final_investment=15000,
                return_amount=20000
            )
            additional_sessions.append(session)
            mock_db.add_session(session)

        ranking = stats_calculator.get_machine_performance_ranking(
            "test_user", min_sessions=2)

        assert ranking['total_machines'] == 2
        # Both machines now have enough sessions
        assert ranking['qualified_machines'] == 2
        assert ranking['min_sessions_required'] == 2

        # Check that rankings exist
        assert 'by_total_profit' in ranking['rankings']
        assert 'by_win_rate' in ranking['rankings']
        assert 'by_avg_profit' in ranking['rankings']
        assert 'by_performance_score' in ranking['rankings']

    def test_analyze_machine_performance(self, stats_calculator, mock_db, sample_sessions):
        """Test detailed machine performance analysis."""
        for session in sample_sessions:
            mock_db.add_session(session)

        analysis = stats_calculator.analyze_machine_performance(
            "test_user", "CR花の慶次")

        assert analysis['machine_name'] == "CR花の慶次"
        assert analysis['has_data'] is True
        assert 'machine_stats' in analysis
        assert 'time_analysis' in analysis
        assert 'store_analysis' in analysis
        assert 'recent_performance' in analysis
        assert 'recommendations' in analysis

        # Check time analysis
        time_analysis = analysis['time_analysis']
        assert 'best_hours' in time_analysis
        assert 'session_distribution' in time_analysis

        # Check store analysis
        store_analysis = analysis['store_analysis']
        assert len(store_analysis) > 0  # Should have store data

        # Check recommendations
        recommendations = analysis['recommendations']
        assert isinstance(recommendations, list)

    def test_analyze_machine_performance_no_data(self, stats_calculator, mock_db):
        """Test machine performance analysis with no data."""
        analysis = stats_calculator.analyze_machine_performance(
            "test_user", "非存在機種")

        assert analysis['machine_name'] == "非存在機種"
        assert analysis['has_data'] is False
        assert analysis['message'] == 'No sessions found for this machine'


class TestStatisticsValidation:
    """Test statistics data validation functionality."""

    def test_validate_stats_data_valid_sessions(self, stats_calculator, sample_sessions):
        """Test validation with valid session data."""
        validation_result = stats_calculator.validate_stats_data(
            sample_sessions)

        assert validation_result['is_valid'] is True
        assert validation_result['total_sessions'] == 4
        assert validation_result['completed_sessions'] == 3
        assert validation_result['incomplete_sessions'] == 1
        assert validation_result['invalid_sessions'] == 0
        assert len(validation_result['errors']) == 0

    def test_validate_stats_data_invalid_sessions(self, stats_calculator):
        """Test validation with invalid session data."""
        # Create a session with missing profit calculation
        invalid_session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        # Manually set as completed but without proper completion
        invalid_session.is_completed = True
        invalid_session.final_investment = 15000
        invalid_session.return_amount = 20000
        # Don't set profit (this should cause validation error)

        validation_result = stats_calculator.validate_stats_data(
            [invalid_session])

        assert validation_result['is_valid'] is False
        assert validation_result['invalid_sessions'] == 1
        assert len(validation_result['errors']) > 0

    def test_validate_stats_data_extreme_values(self, stats_calculator):
        """Test validation with extreme values."""
        extreme_session = GameSession(
            user_id="test_user",
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            store_name="テストホール",
            machine_name="CR花の慶次",
            initial_investment=10000
        )
        extreme_session.complete_session(
            end_time=datetime(2024, 1, 15, 12, 0),
            final_investment=1500000,  # Very high investment
            return_amount=15000000     # Very high return
        )

        validation_result = stats_calculator.validate_stats_data(
            [extreme_session])

        # Should be valid but have warnings
        assert validation_result['is_valid'] is True
        assert len(validation_result['warnings']) > 0

    def test_validate_stats_data_insufficient_data(self, stats_calculator):
        """Test validation with insufficient data."""
        # Create only 2 completed sessions
        sessions = []
        for i in range(2):
            session = GameSession(
                user_id="test_user",
                date=datetime(2024, 1, 15 + i),
                start_time=datetime(2024, 1, 15 + i, 10, 0),
                store_name="テストホール",
                machine_name="CR花の慶次",
                initial_investment=10000
            )
            session.complete_session(
                end_time=datetime(2024, 1, 15 + i, 12, 0),
                final_investment=15000,
                return_amount=20000
            )
            sessions.append(session)

        validation_result = stats_calculator.validate_stats_data(sessions)

        assert validation_result['is_valid'] is True
        assert validation_result['completed_sessions'] == 2
        # Should have warning about limited data
        warning_messages = ' '.join(validation_result['warnings'])
        assert 'Limited data available' in warning_messages


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


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
