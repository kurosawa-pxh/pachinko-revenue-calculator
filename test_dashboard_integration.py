#!/usr/bin/env python3
"""
Integration test for the statistics dashboard implementation.
Tests the complete flow from data to chart generation.
"""

from src.models import GameSession
from src.stats import StatsCalculator
from src.database import DatabaseManager
import sys
import os
import tempfile
import unittest
from datetime import datetime, date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


class TestDashboardIntegration(unittest.TestCase):
    """Test the complete dashboard integration."""

    def setUp(self):
        """Set up test database and components."""
        self.temp_db = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db)
        self.stats_calculator = StatsCalculator(self.db_manager)
        self.user_id = "test_user"

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.temp_db):
            os.unlink(self.temp_db)

    def test_complete_dashboard_flow(self):
        """Test the complete flow from session creation to dashboard display."""
        # Create test sessions
        test_sessions = [
            GameSession(
                user_id=self.user_id,
                date=datetime(2024, 1, 15),
                start_time=datetime(2024, 1, 15, 10, 0),
                end_time=datetime(2024, 1, 15, 14, 0),
                store_name="テスト店舗A",
                machine_name="テスト機種1",
                initial_investment=10000,
                final_investment=15000,
                return_amount=25000,
                profit=10000,
                is_completed=True
            ),
            GameSession(
                user_id=self.user_id,
                date=datetime(2024, 1, 20),
                start_time=datetime(2024, 1, 20, 11, 0),
                end_time=datetime(2024, 1, 20, 15, 0),
                store_name="テスト店舗B",
                machine_name="テスト機種2",
                initial_investment=20000,
                final_investment=30000,
                return_amount=20000,
                profit=-10000,
                is_completed=True
            ),
            GameSession(
                user_id=self.user_id,
                date=datetime(2024, 2, 5),
                start_time=datetime(2024, 2, 5, 12, 0),
                end_time=datetime(2024, 2, 5, 16, 0),
                store_name="テスト店舗A",
                machine_name="テスト機種1",
                initial_investment=15000,
                final_investment=20000,
                return_amount=35000,
                profit=15000,
                is_completed=True
            )
        ]

        # Insert test sessions
        session_ids = []
        for session in test_sessions:
            session_id = self.db_manager.create_session(session)
            session_ids.append(session_id)

        # Test basic statistics
        basic_stats = self.stats_calculator.get_user_basic_stats(self.user_id)
        self.assertEqual(basic_stats.completed_sessions, 3)
        # 10000 - 10000 + 15000
        self.assertEqual(basic_stats.total_profit, 15000)
        self.assertAlmostEqual(basic_stats.win_rate, 66.67,
                               places=1)  # 2 wins out of 3

        # Test basic stats chart generation
        charts = self.stats_calculator.generate_basic_stats_charts(basic_stats)
        self.assertIn('total_profit', charts)
        self.assertIn('win_rate', charts)
        self.assertIn('session_summary', charts)
        self.assertIn('averages', charts)
        self.assertIn('profit_range', charts)

        # Test monthly statistics
        monthly_stats = self.stats_calculator.get_monthly_stats_range(
            self.user_id, 2024, 1, 2024, 2
        )
        self.assertEqual(len(monthly_stats), 2)  # January and February

        # Test monthly chart generation
        monthly_chart = self.stats_calculator.generate_monthly_stats_chart(
            monthly_stats)
        self.assertIsNotNone(monthly_chart)

        # Test machine statistics
        machine_stats = self.stats_calculator.get_all_machine_stats(
            self.user_id)
        self.assertEqual(len(machine_stats), 2)  # Two different machines

        # Test machine chart generation
        machine_chart = self.stats_calculator.generate_machine_stats_chart(
            machine_stats, min_sessions=1)
        self.assertIsNotNone(machine_chart)

        print("✅ Complete dashboard integration test passed!")

    def test_empty_data_handling(self):
        """Test dashboard behavior with no data."""
        # Test basic stats with no data
        basic_stats = self.stats_calculator.get_user_basic_stats(self.user_id)
        self.assertEqual(basic_stats.completed_sessions, 0)
        self.assertEqual(basic_stats.total_profit, 0)

        # Test chart generation with empty data
        charts = self.stats_calculator.generate_basic_stats_charts(basic_stats)
        self.assertIn('total_profit', charts)
        self.assertIn('win_rate', charts)

        # Test monthly chart with empty data
        monthly_chart = self.stats_calculator.generate_monthly_stats_chart([])
        self.assertIsNotNone(monthly_chart)

        # Test machine chart with empty data
        machine_chart = self.stats_calculator.generate_machine_stats_chart([])
        self.assertIsNotNone(machine_chart)

        print("✅ Empty data handling test passed!")

    def test_insufficient_data_warnings(self):
        """Test warning messages for insufficient data."""
        # Create one session (insufficient for meaningful statistics)
        session = GameSession(
            user_id=self.user_id,
            date=datetime(2024, 1, 15),
            start_time=datetime(2024, 1, 15, 10, 0),
            end_time=datetime(2024, 1, 15, 14, 0),
            store_name="テスト店舗",
            machine_name="テスト機種",
            initial_investment=10000,
            final_investment=15000,
            return_amount=20000,
            profit=5000,
            is_completed=True
        )

        session_id = self.db_manager.create_session(session)

        # Test machine chart with insufficient data
        machine_stats = self.stats_calculator.get_all_machine_stats(
            self.user_id)
        machine_chart = self.stats_calculator.generate_machine_stats_chart(
            machine_stats, min_sessions=3)

        # Chart should be generated but with warning message
        self.assertIsNotNone(machine_chart)

        print("✅ Insufficient data warnings test passed!")


if __name__ == '__main__':
    unittest.main()
