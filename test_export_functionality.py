"""
Test script for export functionality.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd

from src.models import GameSession
from src.database import DatabaseManager
from src.stats import StatsCalculator
from src.export import ExportManager, ExportError


class TestExportFunctionality:
    """Test class for export functionality."""

    def setup_method(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        self.db_manager = DatabaseManager(self.temp_db.name)
        self.stats_calculator = StatsCalculator(self.db_manager)
        self.export_manager = ExportManager(self.stats_calculator)

        # Create test sessions
        self.test_sessions = self._create_test_sessions()

        # Save test sessions to database
        for session in self.test_sessions:
            self.db_manager.create_session(session)

    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def _create_test_sessions(self):
        """Create test game sessions."""
        sessions = []
        base_date = datetime.now() - timedelta(days=30)

        for i in range(10):
            session_date = base_date + timedelta(days=i * 3)

            # Create completed session
            session = GameSession(
                user_id="test_user",
                date=session_date,
                start_time=session_date.replace(hour=10, minute=0),
                store_name=f"テスト店舗{i % 3 + 1}",
                machine_name=f"テスト機種{i % 4 + 1}",
                initial_investment=1000 + (i * 100)
            )

            # Complete the session
            end_time = session_date.replace(hour=14, minute=30)
            final_investment = session.initial_investment + (i * 50)
            return_amount = final_investment + \
                ((-1) ** i) * (i * 200)  # Alternating profit/loss

            session.complete_session(end_time, final_investment, return_amount)
            sessions.append(session)

        # Add one incomplete session
        incomplete_session = GameSession(
            user_id="test_user",
            date=datetime.now(),
            start_time=datetime.now().replace(hour=10, minute=0),
            store_name="進行中店舗",
            machine_name="進行中機種",
            initial_investment=2000
        )
        sessions.append(incomplete_session)

        return sessions

    def test_csv_export_basic(self):
        """Test basic CSV export functionality."""
        # Get completed sessions only
        completed_sessions = [s for s in self.test_sessions if s.is_completed]

        # Export to CSV
        csv_data = self.export_manager.export_to_csv(completed_sessions)

        # Verify CSV data
        assert isinstance(csv_data, bytes)
        assert len(csv_data) > 0

        # Parse CSV and verify content
        csv_string = csv_data.decode('utf-8-sig')
        lines = csv_string.strip().split('\n')

        # Check header
        header = lines[0]
        expected_columns = ['ID', '日付', '開始時間', '終了時間', '店舗名', '機種名',
                            '開始投資額', '最終投資額', '回収金額', '収支', '完了状態',
                            '作成日時', '更新日時']

        for col in expected_columns:
            assert col in header

        # Check data rows (should be 10 completed sessions)
        assert len(lines) == 11  # Header + 10 data rows

    def test_csv_export_with_incomplete(self):
        """Test CSV export including incomplete sessions."""
        # Export all sessions including incomplete
        csv_data = self.export_manager.export_to_csv(
            self.test_sessions, include_incomplete=True)

        # Parse CSV
        csv_string = csv_data.decode('utf-8-sig')
        lines = csv_string.strip().split('\n')

        # Should include all 11 sessions (10 completed + 1 incomplete)
        assert len(lines) == 12  # Header + 11 data rows

    def test_csv_export_empty_sessions(self):
        """Test CSV export with empty session list."""
        with pytest.raises(ExportError) as exc_info:
            self.export_manager.export_to_csv([])

        assert "エクスポートするデータがありません" in str(exc_info.value)

    def test_pdf_export_basic(self):
        """Test basic PDF export functionality."""
        # Get completed sessions only
        completed_sessions = [s for s in self.test_sessions if s.is_completed]

        # Export to PDF
        pdf_data = self.export_manager.export_to_pdf(
            completed_sessions, "test_user")

        # Verify PDF data
        assert isinstance(pdf_data, bytes)
        assert len(pdf_data) > 0

        # Check PDF header (basic validation)
        assert pdf_data.startswith(b'%PDF')

    def test_pdf_export_with_stats(self):
        """Test PDF export with statistics included."""
        completed_sessions = [s for s in self.test_sessions if s.is_completed]

        # Export with stats
        pdf_data = self.export_manager.export_to_pdf(
            completed_sessions, "test_user", include_stats=True
        )

        assert isinstance(pdf_data, bytes)
        assert len(pdf_data) > 0
        assert pdf_data.startswith(b'%PDF')

    def test_pdf_export_without_stats(self):
        """Test PDF export without statistics."""
        completed_sessions = [s for s in self.test_sessions if s.is_completed]

        # Export without stats
        pdf_data = self.export_manager.export_to_pdf(
            completed_sessions, "test_user", include_stats=False
        )

        assert isinstance(pdf_data, bytes)
        assert len(pdf_data) > 0
        assert pdf_data.startswith(b'%PDF')

    def test_export_validation(self):
        """Test export data validation."""
        # Test with valid data
        validation_result = self.export_manager.validate_export_data(
            self.test_sessions)

        assert validation_result['is_valid'] is True
        assert validation_result['session_count'] == 11
        assert validation_result['completed_count'] == 10
        assert validation_result['incomplete_count'] == 1
        # Should warn about incomplete sessions
        assert len(validation_result['warnings']) > 0

    def test_export_validation_empty(self):
        """Test export validation with empty data."""
        validation_result = self.export_manager.validate_export_data([])

        assert validation_result['is_valid'] is False
        assert len(validation_result['errors']) > 0
        assert validation_result['session_count'] == 0

    def test_filename_generation(self):
        """Test export filename generation."""
        # Test without date range
        filename = self.export_manager.generate_export_filename(
            'csv', 'test_user')
        assert filename.endswith('.csv')
        assert 'pachinko_data_all_' in filename

        # Test with date range
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        filename = self.export_manager.generate_export_filename(
            'pdf', 'test_user', (start_date, end_date)
        )
        assert filename.endswith('.pdf')
        assert start_date.strftime('%Y%m%d') in filename
        assert end_date.strftime('%Y%m%d') in filename

    def test_export_summary(self):
        """Test export summary generation."""
        summary = self.export_manager.get_export_summary(self.test_sessions)

        assert summary['total_sessions'] == 11
        assert summary['completed_sessions'] == 10
        assert summary['incomplete_sessions'] == 1
        assert 'date_range' in summary
        assert 'total_profit' in summary
        assert 'csv_size_estimate' in summary
        assert 'pdf_size_estimate' in summary

    def test_export_summary_empty(self):
        """Test export summary with empty data."""
        summary = self.export_manager.get_export_summary([])

        assert summary['total_sessions'] == 0
        assert summary['completed_sessions'] == 0
        assert summary['date_range'] is None
        assert summary['total_profit'] == 0


def test_csv_export_integration():
    """Integration test for CSV export."""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        db_manager = DatabaseManager(temp_db.name)
        stats_calculator = StatsCalculator(db_manager)
        export_manager = ExportManager(stats_calculator)

        # Create and save a test session
        session = GameSession(
            user_id="integration_test",
            date=datetime.now(),
            start_time=datetime.now().replace(hour=10, minute=0),
            store_name="統合テスト店舗",
            machine_name="統合テスト機種",
            initial_investment=1000
        )

        # Complete the session
        session.complete_session(
            datetime.now().replace(hour=14, minute=0),
            1500,
            2000
        )

        # Save to database
        db_manager.create_session(session)

        # Retrieve and export
        sessions = db_manager.get_sessions("integration_test")
        csv_data = export_manager.export_to_csv(sessions)

        # Verify
        assert isinstance(csv_data, bytes)
        assert len(csv_data) > 0

        # Parse and check content
        csv_string = csv_data.decode('utf-8-sig')
        assert "統合テスト店舗" in csv_string
        assert "統合テスト機種" in csv_string
        assert "500" in csv_string  # Profit

    finally:
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)


def test_pdf_export_integration():
    """Integration test for PDF export."""
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()

    try:
        db_manager = DatabaseManager(temp_db.name)
        stats_calculator = StatsCalculator(db_manager)
        export_manager = ExportManager(stats_calculator)

        # Create and save test sessions
        for i in range(3):
            session = GameSession(
                user_id="pdf_test",
                date=datetime.now() - timedelta(days=i),
                start_time=datetime.now().replace(hour=10, minute=0),
                store_name=f"PDF店舗{i+1}",
                machine_name=f"PDF機種{i+1}",
                initial_investment=1000 + (i * 100)
            )

            # Complete the session
            session.complete_session(
                datetime.now().replace(hour=14, minute=0),
                session.initial_investment + 200,
                session.initial_investment + 200 + (i * 100)
            )

            db_manager.create_session(session)

        # Retrieve and export
        sessions = db_manager.get_sessions("pdf_test")
        pdf_data = export_manager.export_to_pdf(
            sessions, "pdf_test", include_stats=True)

        # Verify
        assert isinstance(pdf_data, bytes)
        assert len(pdf_data) > 0
        assert pdf_data.startswith(b'%PDF')

    finally:
        if os.path.exists(temp_db.name):
            os.unlink(temp_db.name)


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestExportFunctionality()
    test_instance.setup_method()

    try:
        print("Testing CSV export...")
        test_instance.test_csv_export_basic()
        print("✅ CSV export test passed")

        print("Testing PDF export...")
        test_instance.test_pdf_export_basic()
        print("✅ PDF export test passed")

        print("Testing export validation...")
        test_instance.test_export_validation()
        print("✅ Export validation test passed")

        print("Testing integration...")
        test_csv_export_integration()
        test_pdf_export_integration()
        print("✅ Integration tests passed")

        print("\n🎉 All export functionality tests passed!")

    finally:
        test_instance.teardown_method()
