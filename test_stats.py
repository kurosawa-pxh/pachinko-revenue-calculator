"""
Test suite for the statistics calculation engine.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from typing import List

from src.database import DatabaseManager
from src.models import GameSession
from src.stats import StatsCalculator, BasicStats, MonthlyStats, MachineStats


class TestStatsCalculator:
    """Test cases for StatsCalculator class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)

    @pytest.fixture
    def db_manager(self, temp_db):
        """Create a database manager with temporary database."""
        return DatabaseManager(temp_db)

    @pytest.fixture
    def stats_calculator(self, db_manager):
        """Create a stats calculator instance."""
        return StatsCalculator(db_manager)

    @pytest.fixture
    def sample_sessions(self):
        """Create sample game sessions for testing."""
        base_date = datetime(2024, 1, 15)
        sessions = []

        # Create completed sessions with various outcomes
        session_data = [
            # Winning sessions
            {"profit": 15000, "investment": 20000, "return": 35000,
                "machine": "CR花の慶次", "store": "パチンコ店A"},
            {"profit": 8000, "investment": 15000, "return": 23000,
                "machine": "CR花の慶次", "store": "パチンコ店A"},
            {"profit": 25000, "investment": 30000, "return": 55000,
                "machine": "CRぱちんこ必殺仕事人", "store": "パチンコ店B"},

            # Losing sessions
            {"profit": -10000, "investment": 25000, "return": 15000,
                "machine": "CR花の慶次", "store": "パチンコ店A"},
            {"profit": -15000, "investment": 20000, "return": 5000,
                "machine": "CRぱちんこ必殺仕事人", "store": "パチンコ店B"},
            {"profit": -5000, "investment": 10000, "return": 5000,
                "machine": "CR北斗の拳", "store": "パチンコ店C"},
        ]

        for i, data in enumerate(session_data):
            session_date = base_date + timedelta(days=i)
            session = GameSession(
                user_id="test_user",
                date=session_date,
                start_time=session_date.replace(hour=14, minute=0),
                store_name=data["store"],
                machine_name=data["machine"],
                initial_investment=data["investment"] -
                5000,  # Simulate initial amount
                id=i + 1
            )

            # Complete the session
            end_time = session_date.replace(hour=18, minute=0)
            session.complete_session(
                end_time, data["investment"], data["return"])
            sessions.append(session)

        # Add one incomplete session
        incomplete_session = GameSession(
            user_id="test_user",
            date=base_date + timedelta(days=len(session_data)),
            start_time=(base_date + timedelta(days=len(session_data))
                        ).replace(hour=15, minute=0),
            store_name="パチンコ店A",
            machine_name="CR花の慶次",
            initial_investment=10000,
            id=len(session_data) + 1
        )
        sessions.append(incomplete_session)

        return sessions

    def test_calculate_session_profit(self, stats_calculator):
        """Test session profit calculation."""
        # Test positive profit
        profit = stats_calculator.calculate_session_profit(20000, 35000)
        assert profit == 15000

        # Test negative profit (loss)
        profit = stats_calculator.calculate_session_profit(25000, 15000)
        assert profit == -10000

        # Test break-even
        profit = stats_calculator.calculate_session_profit(20000, 20000)
        assert profit == 0

    def test_calculate_basic_stats(self, stats_calculator, sample_sessions):
        """Test basic statistics calculation."""
        stats = stats_calculator.calculate_basic_stats(sample_sessions)

        assert isinstance(stats, BasicStats)
        assert stats.total_sessions == 7  # 6 completed + 1 incomplete
        assert stats.completed_sessions == 6  # Only completed sessions
        assert stats.winning_sessions == 3
        assert stats.losing_sessions == 3
        assert stats.win_rate == 50.0  # 3/6 * 100

        # Check totals
        expected_total_profit = 15000 + 8000 + 25000 - 10000 - 15000 - 5000
        assert stats.total_profit == expected_total_profit

        expected_total_investment = 20000 + 15000 + 30000 + 25000 + 20000 + 10000
        assert stats.total_investment == expected_total_investment

        # Check averages
        assert stats.avg_investment == expected_total_investment / 6
        assert stats.avg_profit == expected_total_profit / 6

    def test_calculate_basic_stats_empty(self, stats_calculator):
        """Test basic statistics with empty session list."""
        stats = stats_calculator.calculate_basic_stats([])

        assert stats.total_sessions == 0
        assert stats.completed_sessions == 0
        assert stats.total_profit == 0
        assert stats.win_rate == 0.0

    def test_calculate_machine_stats(self, stats_calculator, sample_sessions):
        """Test machine-specific statistics calculation."""
        machine_stats = stats_calculator.calculate_machine_stats(
            sample_sessions, "CR花の慶次")

        assert isinstance(machine_stats, MachineStats)
        assert machine_stats.machine_name == "CR花の慶次"
        # CR花の慶次 appears in 4 total sessions (3 completed + 1 incomplete)
        assert machine_stats.basic_stats.total_sessions == 4
        assert machine_stats.basic_stats.completed_sessions == 3  # 3 completed sessions

        # Check store distribution - all 4 sessions are at パチンコ店A
        assert "パチンコ店A" in machine_stats.store_distribution
        assert machine_stats.store_distribution["パチンコ店A"] == 4

        # Test with non-existent machine
        empty_stats = stats_calculator.calculate_machine_stats(
            sample_sessions, "NonExistent")
        assert empty_stats.basic_stats.total_sessions == 0

    def test_monthly_stats_calculation(self, stats_calculator, db_manager, sample_sessions):
        """Test monthly statistics calculation."""
        # Save sessions to database
        for session in sample_sessions:
            if session.is_completed:
                db_manager.create_session(session)

        # Calculate monthly stats for January 2024
        monthly_stats = stats_calculator.calculate_monthly_stats(
            "test_user", 2024, 1)

        assert isinstance(monthly_stats, MonthlyStats)
        assert monthly_stats.year == 2024
        assert monthly_stats.month == 1
        assert monthly_stats.basic_stats.completed_sessions > 0

        # Check daily breakdown
        assert len(monthly_stats.daily_profits) > 0
        assert len(monthly_stats.sessions_by_day) > 0

    def test_monthly_stats_invalid_month(self, stats_calculator):
        """Test monthly stats with invalid month."""
        with pytest.raises(ValueError, match="Invalid month"):
            stats_calculator.calculate_monthly_stats("test_user", 2024, 13)

        with pytest.raises(ValueError, match="Invalid month"):
            stats_calculator.calculate_monthly_stats("test_user", 2024, 0)

    def test_monthly_stats_invalid_year(self, stats_calculator):
        """Test monthly stats with invalid year."""
        with pytest.raises(ValueError, match="Invalid year"):
            stats_calculator.calculate_monthly_stats("test_user", 1999, 1)

        with pytest.raises(ValueError, match="Invalid year"):
            stats_calculator.calculate_monthly_stats("test_user", 2030, 1)

    def test_get_all_machine_stats(self, stats_calculator, db_manager, sample_sessions):
        """Test getting statistics for all machines."""
        # Save sessions to database
        for session in sample_sessions:
            if session.is_completed:
                db_manager.create_session(session)

        machine_stats_list = stats_calculator.get_all_machine_stats(
            "test_user")

        assert len(machine_stats_list) == 3  # Three different machines

        # Should be sorted by total sessions (descending)
        assert machine_stats_list[0].basic_stats.total_sessions >= machine_stats_list[1].basic_stats.total_sessions

        # Check that all machines are represented
        machine_names = [stats.machine_name for stats in machine_stats_list]
        assert "CR花の慶次" in machine_names
        assert "CRぱちんこ必殺仕事人" in machine_names
        assert "CR北斗の拳" in machine_names

    def test_machine_performance_ranking(self, stats_calculator, db_manager, sample_sessions):
        """Test machine performance ranking."""
        # Save sessions to database
        for session in sample_sessions:
            if session.is_completed:
                db_manager.create_session(session)

        ranking = stats_calculator.get_machine_performance_ranking(
            "test_user", min_sessions=1)

        assert "total_machines" in ranking
        assert "qualified_machines" in ranking
        assert "rankings" in ranking

        rankings = ranking["rankings"]
        assert "by_total_profit" in rankings
        assert "by_win_rate" in rankings
        assert "by_avg_profit" in rankings

        # Check that rankings are properly sorted
        profit_ranking = rankings["by_total_profit"]
        if len(profit_ranking) > 1:
            assert profit_ranking[0].basic_stats.total_profit >= profit_ranking[1].basic_stats.total_profit

    def test_analyze_machine_performance(self, stats_calculator, db_manager, sample_sessions):
        """Test detailed machine performance analysis."""
        # Save sessions to database
        for session in sample_sessions:
            if session.is_completed:
                db_manager.create_session(session)

        analysis = stats_calculator.analyze_machine_performance(
            "test_user", "CR花の慶次")

        assert analysis["has_data"] is True
        assert analysis["machine_name"] == "CR花の慶次"
        assert "machine_stats" in analysis
        assert "time_analysis" in analysis
        assert "store_analysis" in analysis
        assert "recent_performance" in analysis
        assert "recommendations" in analysis

        # Test with non-existent machine
        empty_analysis = stats_calculator.analyze_machine_performance(
            "test_user", "NonExistent")
        assert empty_analysis["has_data"] is False

    def test_filter_sessions_by_period(self, stats_calculator, sample_sessions):
        """Test session filtering by date period."""
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 18)

        filtered_sessions = stats_calculator.filter_sessions_by_period(
            sample_sessions, start_date, end_date)

        # Should include sessions from 15th, 16th, 17th (end_date is exclusive)
        assert len(filtered_sessions) == 3

        # All filtered sessions should be within the date range
        for session in filtered_sessions:
            assert start_date.date() <= session.date.date() < end_date.date()

    def test_validate_stats_data(self, stats_calculator, sample_sessions):
        """Test statistics data validation."""
        validation_result = stats_calculator.validate_stats_data(
            sample_sessions)

        assert "is_valid" in validation_result
        assert "warnings" in validation_result
        assert "errors" in validation_result
        assert "total_sessions" in validation_result
        assert "completed_sessions" in validation_result

        assert validation_result["total_sessions"] == len(sample_sessions)
        # 6 completed sessions
        assert validation_result["completed_sessions"] == 6

    def test_trend_calculation(self, stats_calculator):
        """Test trend calculation helper method."""
        # Test increasing trend
        increasing_values = [10, 15, 20, 25, 30]
        trend = stats_calculator._calculate_trend(increasing_values)
        assert trend == "increasing"

        # Test decreasing trend
        decreasing_values = [30, 25, 20, 15, 10]
        trend = stats_calculator._calculate_trend(decreasing_values)
        assert trend == "decreasing"

        # Test stable trend
        stable_values = [20, 20, 20, 20, 20]
        trend = stats_calculator._calculate_trend(stable_values)
        assert trend == "stable"

        # Test insufficient data
        insufficient_values = [20]
        trend = stats_calculator._calculate_trend(insufficient_values)
        assert trend == "insufficient_data"

    def test_volatility_calculation(self, stats_calculator):
        """Test volatility calculation helper method."""
        # Test with known values
        values = [10, 20, 30, 40, 50]
        volatility = stats_calculator._calculate_volatility(values)
        assert volatility > 0

        # Test with identical values (should have 0 volatility)
        identical_values = [25, 25, 25, 25, 25]
        volatility = stats_calculator._calculate_volatility(identical_values)
        assert volatility == 0.0

        # Test with insufficient data
        insufficient_values = [20]
        volatility = stats_calculator._calculate_volatility(
            insufficient_values)
        assert volatility == 0.0

    def test_monthly_comparison(self, stats_calculator, db_manager, sample_sessions):
        """Test monthly comparison functionality."""
        # Save sessions to database
        for session in sample_sessions:
            if session.is_completed:
                db_manager.create_session(session)

        # Compare January 2024 with itself (minimal test)
        months = [(2024, 1)]
        comparison = stats_calculator.get_monthly_comparison(
            "test_user", months)

        assert "months_data" in comparison
        assert "profit_trend" in comparison
        assert "total_profit" in comparison
        assert len(comparison["months_data"]) == 1

    def test_monthly_stats_range(self, stats_calculator, db_manager, sample_sessions):
        """Test monthly statistics range calculation."""
        # Save sessions to database
        for session in sample_sessions:
            if session.is_completed:
                db_manager.create_session(session)

        # Get stats for January 2024 only
        monthly_stats = stats_calculator.get_monthly_stats_range(
            "test_user", 2024, 1, 2024, 1)

        assert len(monthly_stats) == 1
        assert monthly_stats[0].year == 2024
        assert monthly_stats[0].month == 1

        # Test invalid range
        with pytest.raises(ValueError, match="Start date must be before"):
            stats_calculator.get_monthly_stats_range(
                "test_user", 2024, 2, 2024, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
