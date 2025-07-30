"""
Export Manager for the Pachinko Revenue Calculator application.

Handles data export functionality including CSV and PDF report generation.
"""

import pandas as pd
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import GameSession
from .stats import StatsCalculator


class ExportError(Exception):
    """Custom exception for export-related errors."""
    pass


class ExportManager:
    """
    Manages data export functionality for the Pachinko Revenue Calculator.

    Provides methods for exporting session data to CSV format and generating
    comprehensive PDF reports with statistics and visualizations.
    """

    def __init__(self, stats_calculator: StatsCalculator):
        """
        Initialize the Export Manager.

        Args:
            stats_calculator: Statistics calculator instance for generating report data
        """
        self.stats_calculator = stats_calculator
        self.logger = logging.getLogger(__name__)

    def export_to_csv(self, sessions: List[GameSession], include_incomplete: bool = False) -> bytes:
        """
        Export game sessions to CSV format.

        Args:
            sessions: List of GameSession objects to export
            include_incomplete: Whether to include incomplete sessions

        Returns:
            bytes: CSV data as bytes

        Raises:
            ExportError: If CSV export fails
        """
        try:
            if not sessions:
                raise ExportError("エクスポートするデータがありません")

            # Filter sessions if needed
            if not include_incomplete:
                sessions = [s for s in sessions if s.is_completed]

            if not sessions:
                raise ExportError("完了したセッションがありません")

            # Convert sessions to DataFrame
            data = []
            for session in sessions:
                row = {
                    'ID': session.id,
                    '日付': session.date.strftime('%Y-%m-%d') if session.date else '',
                    '開始時間': session.start_time.strftime('%H:%M') if session.start_time else '',
                    '終了時間': session.end_time.strftime('%H:%M') if session.end_time else '',
                    '店舗名': session.store_name,
                    '機種名': session.machine_name,
                    '開始投資額': session.initial_investment,
                    '最終投資額': session.final_investment if session.final_investment is not None else '',
                    '回収金額': session.return_amount if session.return_amount is not None else '',
                    '収支': session.profit if session.profit is not None else '',
                    '完了状態': '完了' if session.is_completed else '進行中',
                    '作成日時': session.created_at.strftime('%Y-%m-%d %H:%M:%S') if session.created_at else '',
                    '更新日時': session.updated_at.strftime('%Y-%m-%d %H:%M:%S') if session.updated_at else ''
                }
                data.append(row)

            # Create DataFrame
            df = pd.DataFrame(data)

            # Convert to CSV bytes
            csv_buffer = BytesIO()
            # BOM for Excel compatibility
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_bytes = csv_buffer.getvalue()

            self.logger.info(
                f"Successfully exported {len(sessions)} sessions to CSV")
            return csv_bytes

        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            raise ExportError(f"CSVエクスポートに失敗しました: {e}")

    def export_to_pdf(self, sessions: List[GameSession], user_id: str,
                      include_stats: bool = True, include_charts: bool = False) -> bytes:
        """
        Export game sessions and statistics to PDF format.

        Args:
            sessions: List of GameSession objects to export
            user_id: User ID for generating statistics
            include_stats: Whether to include statistics section
            include_charts: Whether to include chart visualizations (not implemented yet)

        Returns:
            bytes: PDF data as bytes

        Raises:
            ExportError: If PDF export fails
        """
        try:
            if not sessions:
                raise ExportError("エクスポートするデータがありません")

            # Create PDF buffer
            pdf_buffer = BytesIO()

            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Build PDF content
            story = []

            # Add title and header
            story.extend(self._create_pdf_header(user_id, len(sessions)))

            # Add summary statistics if requested
            if include_stats:
                completed_sessions = [s for s in sessions if s.is_completed]
                if completed_sessions:
                    basic_stats = self.stats_calculator.get_user_basic_stats(
                        user_id)
                    story.extend(self._create_pdf_stats_section(basic_stats))

            # Add session details table
            story.extend(self._create_pdf_sessions_table(sessions))

            # Build PDF
            doc.build(story)

            pdf_bytes = pdf_buffer.getvalue()

            self.logger.info(
                f"Successfully exported {len(sessions)} sessions to PDF")
            return pdf_bytes

        except Exception as e:
            self.logger.error(f"PDF export failed: {e}")
            raise ExportError(f"PDFエクスポートに失敗しました: {e}")

    def _create_pdf_header(self, user_id: str, session_count: int) -> List:
        """Create PDF header section."""
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=HexColor('#8A2BE2')
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=HexColor('#00BFFF')
        )

        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            alignment=TA_CENTER
        )

        story = []

        # Title
        story.append(Paragraph("🎰 勝てるクン - 遊技記録レポート", title_style))
        story.append(Paragraph("パチンコ収支管理システム", subtitle_style))

        # Report info
        export_date = datetime.now().strftime('%Y年%m月%d日 %H:%M')
        story.append(Paragraph(f"エクスポート日時: {export_date}", info_style))
        story.append(Paragraph(f"対象セッション数: {session_count}件", info_style))
        story.append(Spacer(1, 20))

        return story

    def _create_pdf_stats_section(self, basic_stats) -> List:
        """Create PDF statistics section."""
        styles = getSampleStyleSheet()

        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=15,
            textColor=HexColor('#FFD700')
        )

        story = []
        story.append(Paragraph("📊 統計サマリー", section_style))

        # Create statistics table
        stats_data = [
            ['項目', '値'],
            ['総セッション数', f"{basic_stats.total_sessions}回"],
            ['完了セッション数', f"{basic_stats.completed_sessions}回"],
            ['総投資額', f"{basic_stats.total_investment:,}円"],
            ['総回収額', f"{basic_stats.total_return:,}円"],
            ['総収支', f"{basic_stats.total_profit:+,}円"],
            ['勝ちセッション', f"{basic_stats.winning_sessions}回"],
            ['負けセッション', f"{basic_stats.losing_sessions}回"],
            ['勝率', f"{basic_stats.win_rate:.1f}%"],
            ['平均投資額', f"{basic_stats.avg_investment:,.0f}円"],
            ['平均収支', f"{basic_stats.avg_profit:+,.0f}円"],
            ['最高収支', f"{basic_stats.max_profit:+,}円"],
            ['最低収支', f"{basic_stats.min_profit:+,}円"]
        ]

        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#8A2BE2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')])
        ]))

        story.append(stats_table)
        story.append(Spacer(1, 20))

        return story

    def _create_pdf_sessions_table(self, sessions: List[GameSession]) -> List:
        """Create PDF sessions table."""
        styles = getSampleStyleSheet()

        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=18,
            spaceAfter=15,
            textColor=HexColor('#FFD700')
        )

        story = []
        story.append(Paragraph("📋 遊技記録詳細", section_style))

        # Prepare table data
        table_data = [
            ['日付', '店舗名', '機種名', '投資額', '回収額', '収支', '状態']
        ]

        for session in sessions:
            row = [
                session.date.strftime('%m/%d') if session.date else '',
                session.store_name[:10] +
                '...' if len(session.store_name) > 10 else session.store_name,
                session.machine_name[:12] + '...' if len(
                    session.machine_name) > 12 else session.machine_name,
                f"{session.final_investment:,}円" if session.final_investment is not None else f"{session.initial_investment:,}円",
                f"{session.return_amount:,}円" if session.return_amount is not None else '-',
                f"{session.profit:+,}円" if session.profit is not None else '-',
                '完了' if session.is_completed else '進行中'
            ]
            table_data.append(row)

        # Create table with appropriate column widths
        col_widths = [0.8*inch, 1.2*inch, 1.3 *
                      inch, 1*inch, 1*inch, 1*inch, 0.7*inch]
        sessions_table = Table(table_data, colWidths=col_widths)

        # Apply table styling
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#8A2BE2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            # Store and machine names left-aligned
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),
            ('ALIGN', (3, 1), (5, -1), 'RIGHT'),  # Numbers right-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#F5F5F5')),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')])
        ]

        # Add profit-based coloring for profit column
        for i, session in enumerate(sessions, 1):
            if session.profit is not None:
                if session.profit > 0:
                    table_style.append(
                        ('TEXTCOLOR', (5, i), (5, i), HexColor('#00AA00')))
                elif session.profit < 0:
                    table_style.append(
                        ('TEXTCOLOR', (5, i), (5, i), HexColor('#CC0000')))

        sessions_table.setStyle(TableStyle(table_style))

        story.append(sessions_table)
        story.append(Spacer(1, 20))

        # Add footer note
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=HexColor('#666666')
        )

        story.append(Paragraph("※ このレポートは勝てるクンによって自動生成されました", note_style))

        return story

    def validate_export_data(self, sessions: List[GameSession]) -> Dict[str, Any]:
        """
        Validate data before export.

        Args:
            sessions: List of GameSession objects to validate

        Returns:
            dict: Validation results with warnings and errors
        """
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'session_count': len(sessions),
                'completed_count': 0,
                'incomplete_count': 0
            }

            if not sessions:
                validation_result['is_valid'] = False
                validation_result['errors'].append("エクスポートするデータがありません")
                return validation_result

            # Count session types
            completed_sessions = [s for s in sessions if s.is_completed]
            incomplete_sessions = [s for s in sessions if not s.is_completed]

            validation_result['completed_count'] = len(completed_sessions)
            validation_result['incomplete_count'] = len(incomplete_sessions)

            # Check for incomplete sessions
            if incomplete_sessions:
                validation_result['warnings'].append(
                    f"{len(incomplete_sessions)}件の未完了セッションが含まれています"
                )

            # Check for sessions with missing data
            sessions_with_missing_data = []
            for session in sessions:
                if session.is_completed:
                    if session.final_investment is None or session.return_amount is None:
                        sessions_with_missing_data.append(session.id)

            if sessions_with_missing_data:
                validation_result['warnings'].append(
                    f"データが不完全なセッションがあります: {sessions_with_missing_data}"
                )

            # Check date range
            if completed_sessions:
                dates = [s.date for s in completed_sessions if s.date]
                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    date_range_days = (max_date - min_date).days

                    validation_result['date_range'] = {
                        'start_date': min_date.strftime('%Y-%m-%d'),
                        'end_date': max_date.strftime('%Y-%m-%d'),
                        'days': date_range_days
                    }

                    if date_range_days > 365:
                        validation_result['warnings'].append(
                            f"データ期間が長期間({date_range_days}日)にわたっています"
                        )

            self.logger.info(
                f"Export data validation completed: {validation_result}")
            return validation_result

        except Exception as e:
            self.logger.error(f"Export data validation failed: {e}")
            return {
                'is_valid': False,
                'errors': [f"データ検証中にエラーが発生しました: {e}"],
                'warnings': [],
                'session_count': 0,
                'completed_count': 0,
                'incomplete_count': 0
            }

    def generate_export_filename(self, export_type: str, user_id: str,
                                 date_range: Optional[tuple] = None) -> str:
        """
        Generate appropriate filename for export.

        Args:
            export_type: Type of export ('csv' or 'pdf')
            user_id: User ID
            date_range: Optional tuple of (start_date, end_date)

        Returns:
            str: Generated filename
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if date_range:
                start_date, end_date = date_range
                date_str = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"
                filename = f"pachinko_data_{date_str}_{timestamp}.{export_type}"
            else:
                filename = f"pachinko_data_all_{timestamp}.{export_type}"

            return filename

        except Exception as e:
            self.logger.error(f"Filename generation failed: {e}")
            # Fallback filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"pachinko_export_{timestamp}.{export_type}"

    def get_export_summary(self, sessions: List[GameSession]) -> Dict[str, Any]:
        """
        Get summary information for export preview.

        Args:
            sessions: List of GameSession objects

        Returns:
            dict: Export summary information
        """
        try:
            if not sessions:
                return {
                    'total_sessions': 0,
                    'completed_sessions': 0,
                    'date_range': None,
                    'total_profit': 0,
                    'export_size_estimate': '0 KB'
                }

            completed_sessions = [s for s in sessions if s.is_completed]

            # Calculate basic stats
            total_profit = sum(s.profit or 0 for s in completed_sessions)

            # Get date range
            dates = [s.date for s in sessions if s.date]
            date_range = None
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                date_range = {
                    'start': min_date.strftime('%Y-%m-%d'),
                    'end': max_date.strftime('%Y-%m-%d'),
                    'days': (max_date - min_date).days + 1
                }

            # Estimate export size (rough calculation)
            # CSV: approximately 200 bytes per session
            # PDF: approximately 500 bytes per session + 50KB base
            csv_size_kb = max(1, (len(sessions) * 200) // 1024)
            pdf_size_kb = max(1, ((len(sessions) * 500) + 50000) // 1024)

            return {
                'total_sessions': len(sessions),
                'completed_sessions': len(completed_sessions),
                'incomplete_sessions': len(sessions) - len(completed_sessions),
                'date_range': date_range,
                'total_profit': total_profit,
                'csv_size_estimate': f"{csv_size_kb} KB",
                'pdf_size_estimate': f"{pdf_size_kb} KB"
            }

        except Exception as e:
            self.logger.error(f"Export summary generation failed: {e}")
            return {
                'total_sessions': len(sessions) if sessions else 0,
                'completed_sessions': 0,
                'date_range': None,
                'total_profit': 0,
                'export_size_estimate': 'Unknown',
                'error': str(e)
            }
