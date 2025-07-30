"""
Test responsive design implementation for the Pachinko Revenue Calculator.

Tests the mobile optimization and desktop layout features.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from src.ui_manager import UIManager
from src.database import DatabaseManager
from src.stats import StatsCalculator


class TestResponsiveDesign:
    """Test responsive design features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=DatabaseManager)
        self.mock_stats = Mock(spec=StatsCalculator)

        # Mock Streamlit session state
        with patch('streamlit.session_state', new_callable=dict) as mock_session:
            mock_session.update({
                'current_page': 'home',
                'user_id': 'test_user',
                'active_session': None,
                'form_errors': {}
            })
            self.ui_manager = UIManager(self.mock_db, self.mock_stats)

    @patch('streamlit.markdown')
    def test_handle_responsive_layout(self, mock_markdown):
        """Test responsive layout handling."""
        self.ui_manager.handle_responsive_layout()

        # Verify that responsive JavaScript was added
        mock_markdown.assert_called()
        call_args = mock_markdown.call_args_list

        # Check if JavaScript for screen detection was added
        js_calls = [
            call for call in call_args if 'detectScreenSize' in str(call)]
        assert len(js_calls) > 0, "Screen detection JavaScript should be added"

    @patch('streamlit.markdown')
    def test_optimize_for_touch(self, mock_markdown):
        """Test touch optimization."""
        self.ui_manager.optimize_for_touch()

        # Verify that touch optimization CSS was added
        mock_markdown.assert_called()
        call_args = mock_markdown.call_args_list

        # Check if touch-related CSS was added
        touch_calls = [
            call for call in call_args if 'touch-action' in str(call)]
        assert len(touch_calls) > 0, "Touch optimization CSS should be added"

    @patch('streamlit.markdown')
    def test_handle_orientation_change(self, mock_markdown):
        """Test orientation change handling."""
        self.ui_manager.handle_orientation_change()

        # Verify that orientation change JavaScript was added
        mock_markdown.assert_called()
        call_args = mock_markdown.call_args_list

        # Check if orientation handling JavaScript was added
        orientation_calls = [
            call for call in call_args if 'orientationchange' in str(call)]
        assert len(
            orientation_calls) > 0, "Orientation change handling should be added"

    @patch('streamlit.markdown')
    def test_optimize_for_desktop(self, mock_markdown):
        """Test desktop optimization."""
        self.ui_manager.optimize_for_desktop()

        # Verify that desktop optimization CSS was added
        mock_markdown.assert_called()
        call_args = mock_markdown.call_args_list

        # Check if desktop-specific CSS was added
        desktop_calls = [
            call for call in call_args if 'desktop-layout' in str(call)]
        assert len(desktop_calls) > 0, "Desktop optimization CSS should be added"

    @patch('streamlit.markdown')
    def test_handle_multi_tab_consistency(self, mock_markdown):
        """Test multi-tab consistency handling."""
        self.ui_manager.handle_multi_tab_consistency()

        # Verify that multi-tab sync JavaScript was added
        mock_markdown.assert_called()
        call_args = mock_markdown.call_args_list

        # Check if multi-tab sync JavaScript was added
        multitab_calls = [
            call for call in call_args if 'MultiTabSync' in str(call)]
        assert len(
            multitab_calls) > 0, "Multi-tab sync JavaScript should be added"

    @patch('streamlit.markdown')
    def test_validate_browser_compatibility(self, mock_markdown):
        """Test browser compatibility validation."""
        result = self.ui_manager.validate_browser_compatibility()

        # Should return True and add compatibility check JavaScript
        assert result is True
        mock_markdown.assert_called()

        call_args = mock_markdown.call_args_list
        compat_calls = [
            call for call in call_args if 'checkBrowserCompatibility' in str(call)]
        assert len(
            compat_calls) > 0, "Browser compatibility check should be added"

    def test_get_device_info(self):
        """Test device information retrieval."""
        device_info = self.ui_manager.get_device_info()

        # Should return a dictionary with device information
        assert isinstance(device_info, dict)
        assert 'is_mobile' in device_info
        assert 'is_tablet' in device_info
        assert 'is_desktop' in device_info
        assert 'screen_width' in device_info
        assert 'screen_height' in device_info

    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    def test_render_desktop_dashboard(self, mock_button, mock_columns, mock_markdown):
        """Test desktop dashboard rendering."""
        # Mock database response
        mock_sessions = [
            {'profit': 5000, 'is_completed': True},
            {'profit': -2000, 'is_completed': True},
            {'profit': 3000, 'is_completed': True}
        ]
        self.mock_db.get_sessions_as_dict.return_value = mock_sessions

        # Mock columns
        mock_col = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col, mock_col]

        self.ui_manager.render_desktop_dashboard()

        # Verify database was called
        self.mock_db.get_sessions_as_dict.assert_called_once()

        # Verify columns were created for desktop layout
        mock_columns.assert_called()

        # Verify desktop-specific markup was added
        desktop_calls = [call for call in mock_markdown.call_args_list
                         if 'desktop-layout' in str(call) or 'main-container' in str(call)]
        assert len(desktop_calls) > 0, "Desktop-specific markup should be added"

    @patch('streamlit.info')
    def test_render_desktop_dashboard_no_data(self, mock_info):
        """Test desktop dashboard with no data."""
        # Mock empty database response
        self.mock_db.get_sessions_as_dict.return_value = []

        self.ui_manager.render_desktop_dashboard()

        # Should show info message for no data
        mock_info.assert_called_once()

    def test_profit_color_classes(self):
        """Test profit color class methods work correctly."""
        # Test positive profit
        positive_class = self.ui_manager.get_profit_color_class(5000)
        assert positive_class == "profit-positive"

        # Test negative profit
        negative_class = self.ui_manager.get_profit_color_class(-2000)
        assert negative_class == "profit-negative"

        # Test zero profit
        neutral_class = self.ui_manager.get_profit_color_class(0)
        assert neutral_class == "profit-neutral"

    def test_win_rate_color_classes(self):
        """Test win rate color class methods work correctly."""
        # Test excellent win rate
        excellent_class = self.ui_manager.get_win_rate_color_class(75.0)
        assert excellent_class == "win-rate-excellent"

        # Test good win rate
        good_class = self.ui_manager.get_win_rate_color_class(65.0)
        assert good_class == "win-rate-good"

        # Test average win rate
        average_class = self.ui_manager.get_win_rate_color_class(55.0)
        assert average_class == "win-rate-average"

        # Test poor win rate
        poor_class = self.ui_manager.get_win_rate_color_class(45.0)
        assert poor_class == "win-rate-poor"

        # Test bad win rate
        bad_class = self.ui_manager.get_win_rate_color_class(30.0)
        assert bad_class == "win-rate-bad"


class TestResponsiveCSS:
    """Test responsive CSS implementation."""

    def test_css_file_exists(self):
        """Test that the CSS file exists and contains responsive styles."""
        import os
        css_path = os.path.join('pachinko-app', 'static', 'style.css')
        assert os.path.exists(css_path), "CSS file should exist"

        with open(css_path, 'r', encoding='utf-8') as f:
            css_content = f.read()

        # Check for mobile-first responsive design
        assert '@media (max-width: 768px)' in css_content, "Mobile breakpoint should exist"
        assert '@media (min-width: 769px) and (max-width: 1024px)' in css_content, "Tablet breakpoint should exist"
        assert '@media (min-width: 1025px)' in css_content, "Desktop breakpoint should exist"

        # Check for touch optimization (touch-action is added via JavaScript)
        assert 'pointer: coarse' in css_content, "Touch device CSS should exist"

        # Check for desktop enhancements
        assert 'dashboard-grid' in css_content, "Desktop grid layout should exist"
        assert 'desktop-layout' in css_content, "Desktop layout classes should exist"

        # Check for multi-tab notification styles
        assert 'multi-tab-notification' in css_content, "Multi-tab notification styles should exist"


if __name__ == '__main__':
    pytest.main([__file__])
