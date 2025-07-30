"""
UI Manager for the Pachinko Revenue Calculator application.

Handles Streamlit UI components, page navigation, and user interface logic.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
import logging

from .models import GameSession, ValidationError
from .database import DatabaseManager, DatabaseError
from .stats import StatsCalculator
from .export import ExportManager, ExportError
from .error_handler import handle_error, get_error_handler, safe_execute, UIError, ErrorSeverity


class UIManager:
    """
    Manages the Streamlit user interface for the Pachinko Revenue Calculator.

    Provides methods for rendering different UI components, handling navigation,
    and managing user interactions with proper error handling and validation.
    """

    def __init__(self, db_manager: DatabaseManager, stats_calculator: StatsCalculator):
        """
        Initialize the UI Manager.

        Args:
            db_manager: Database manager instance
            stats_calculator: Statistics calculator instance
        """
        self.db_manager = db_manager
        self.stats_calculator = stats_calculator
        self.export_manager = ExportManager(stats_calculator)
        self.logger = logging.getLogger(__name__)

        # Initialize session state
        self._initialize_session_state()

        # Apply custom styling
        self.apply_custom_styling()

        # Apply responsive design
        self.handle_responsive_layout()
        self.optimize_for_touch()
        self.handle_orientation_change()
        self.optimize_for_desktop()
        self.handle_multi_tab_consistency()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'home'

        if 'user_id' not in st.session_state:
            st.session_state.user_id = 'default_user'  # For now, using default user

        if 'active_session' not in st.session_state:
            st.session_state.active_session = None

        if 'form_errors' not in st.session_state:
            st.session_state.form_errors = {}

    def render_header(self) -> None:
        """Render the application header with navigation."""
        st.markdown("""
        <div class="main-header">
            <h1 style="text-align: center; margin: 0; font-size: 2.5em; 
                       background: linear-gradient(45deg, #FFD700, #FF6B6B);
                       -webkit-background-clip: text;
                       -webkit-text-fill-color: transparent;
                       text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                🎰 勝てるクン 🎰
            </h1>
            <p style="text-align: center; margin: 10px 0 0 0; 
                     color: #F0F0F0; font-size: 1.2em;">
                パチンコ収支管理アプリ
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Navigation menu
        self._render_navigation()

    def _render_navigation(self) -> None:
        """Render the navigation menu."""
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if st.button("🏠 ホーム", key="nav_home", use_container_width=True):
                st.session_state.current_page = 'home'
                st.rerun()

        with col2:
            if st.button("📝 遊技記録", key="nav_record", use_container_width=True):
                st.session_state.current_page = 'record'
                st.rerun()

        with col3:
            if st.button("📊 統計", key="nav_stats", use_container_width=True):
                st.session_state.current_page = 'stats'
                st.rerun()

        with col4:
            if st.button("📋 履歴", key="nav_history", use_container_width=True):
                st.session_state.current_page = 'history'
                st.rerun()

        with col5:
            if st.button("📤 エクスポート", key="nav_export", use_container_width=True):
                st.session_state.current_page = 'export'
                st.rerun()

    def render_main_content(self) -> None:
        """Render the main content based on current page with transition animation."""
        current_page = st.session_state.current_page

        # Add page transition container
        st.markdown('<div class="page-transition">', unsafe_allow_html=True)

        if current_page == 'home':
            self._render_home_page()
        elif current_page == 'record':
            self._render_record_page()
        elif current_page == 'stats':
            self._render_stats_page()
        elif current_page == 'history':
            self._render_history_page()
        elif current_page == 'export':
            self._render_export_page()
        else:
            self.show_animated_error("不明なページです")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_home_page(self) -> None:
        """Render the home page with quick stats and actions."""
        # Check if we should render desktop dashboard
        device_info = self.get_device_info()

        if device_info.get('is_desktop', True):  # Default to desktop for now
            st.markdown("## 🎯 デスクトップダッシュボード")
            self.render_desktop_dashboard()
        else:
            # Mobile/tablet dashboard
            st.markdown("## 🎯 ダッシュボード")
            self._render_mobile_dashboard()

    def _render_mobile_dashboard(self) -> None:
        """Render mobile-optimized dashboard."""
        # Quick stats
        try:
            user_id = st.session_state.user_id
            recent_sessions = self.db_manager.get_sessions_as_dict(
                user_id, limit=10)

            if recent_sessions:
                # Calculate quick stats
                total_profit = sum(session.get('profit', 0)
                                   or 0 for session in recent_sessions)
                completed_sessions = len(
                    [s for s in recent_sessions if s.get('is_completed')])

                col1, col2, col3 = st.columns(3)

                with col1:
                    profit_class = self.get_profit_color_class(total_profit)
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>最近の収支</h3>
                        <p class="{profit_class}" style="font-size: 2em; font-weight: bold;">
                            {total_profit:+,}円
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>完了セッション</h3>
                        <p style="font-size: 2em; font-weight: bold; color: #00BFFF;">
                            {completed_sessions}回
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>総セッション</h3>
                        <p style="font-size: 2em; font-weight: bold; color: #8A2BE2;">
                            {len(recent_sessions)}回
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("まだ遊技記録がありません。「遊技記録」から始めましょう！")

        except DatabaseError as e:
            st.error(f"データベースエラー: {e}")

        # Quick actions
        st.markdown("## 🚀 クイックアクション")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🎮 新しい遊技を開始", key="quick_start", use_container_width=True):
                st.session_state.current_page = 'record'
                st.rerun()

        with col2:
            if st.button("📊 統計を見る", key="quick_stats", use_container_width=True):
                st.session_state.current_page = 'stats'
                st.rerun()

    def _render_record_page(self) -> None:
        """Render the game recording page."""
        st.markdown("## 🎮 遊技記録")

        # Check if there's an active session
        active_session = st.session_state.active_session

        if active_session is None:
            # Show start form
            self._render_session_start_form()
        else:
            # Show end form
            self._render_session_end_form(active_session)

    def _render_stats_page(self) -> None:
        """Render the statistics page with interactive charts."""
        st.markdown("## 📊 統計情報")

        try:
            user_id = st.session_state.user_id

            # Get basic statistics
            basic_stats = self.stats_calculator.get_user_basic_stats(user_id)

            if basic_stats.completed_sessions == 0:
                st.info("📈 まだ完了した遊技記録がありません。遊技記録を追加してから統計を確認してください。")
                return

            # Render basic statistics dashboard
            self._render_basic_stats_dashboard(basic_stats)

            # Add spacing
            st.markdown("---")

            # Render monthly and machine statistics tabs
            tab1, tab2 = st.tabs(["📅 月別統計", "🎰 機種別統計"])

            with tab1:
                self._render_monthly_stats_section(user_id)

            with tab2:
                self._render_machine_stats_section(user_id)

        except DatabaseError as e:
            st.error(f"データベースエラー: {e}")
            self.logger.error(f"Database error in stats page: {e}")
        except Exception as e:
            st.error("統計データの取得中にエラーが発生しました。")
            self.logger.error(f"Unexpected error in stats page: {e}")

    def _render_basic_stats_dashboard(self, basic_stats) -> None:
        """Render the basic statistics dashboard with charts."""
        try:
            # Generate charts
            charts = self.stats_calculator.generate_basic_stats_charts(
                basic_stats)

            # Display total profit prominently
            if 'total_profit' in charts:
                st.plotly_chart(charts['total_profit'],
                                use_container_width=True)

            # Display key metrics in columns
            col1, col2 = st.columns(2)

            with col1:
                if 'win_rate' in charts:
                    st.plotly_chart(charts['win_rate'],
                                    use_container_width=True)

            with col2:
                if 'session_summary' in charts:
                    st.plotly_chart(
                        charts['session_summary'], use_container_width=True)

            # Display additional charts
            col3, col4 = st.columns(2)

            with col3:
                if 'averages' in charts:
                    st.plotly_chart(charts['averages'],
                                    use_container_width=True)

            with col4:
                if 'profit_range' in charts:
                    st.plotly_chart(charts['profit_range'],
                                    use_container_width=True)

            # Display summary statistics in an expander
            with st.expander("📋 詳細統計", expanded=False):
                self._render_detailed_stats_table(basic_stats)

        except Exception as e:
            st.error("基本統計グラフの表示中にエラーが発生しました。")
            self.logger.error(f"Error rendering basic stats dashboard: {e}")

    def _render_detailed_stats_table(self, basic_stats) -> None:
        """Render detailed statistics in a table format."""
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**セッション情報**")
            st.write(f"• 総セッション数: {basic_stats.total_sessions}回")
            st.write(f"• 完了セッション数: {basic_stats.completed_sessions}回")
            st.write(f"• 勝ちセッション: {basic_stats.winning_sessions}回")
            st.write(f"• 負けセッション: {basic_stats.losing_sessions}回")
            st.write(f"• 勝率: {basic_stats.win_rate:.1f}%")

        with col2:
            st.markdown("**収支情報**")
            st.write(f"• 総投資額: {basic_stats.total_investment:,}円")
            st.write(f"• 総回収額: {basic_stats.total_return:,}円")
            st.write(f"• 総収支: {basic_stats.total_profit:+,}円")
            st.write(f"• 平均投資額: {basic_stats.avg_investment:,.0f}円")
            st.write(f"• 平均収支: {basic_stats.avg_profit:+,.0f}円")

        st.markdown("**収支レンジ**")
        col3, col4, col5 = st.columns(3)
        with col3:
            st.metric("最高収支", f"{basic_stats.max_profit:+,}円")
        with col4:
            st.metric("平均収支", f"{basic_stats.avg_profit:+,.0f}円")
        with col5:
            st.metric("最低収支", f"{basic_stats.min_profit:+,}円")

    def _render_monthly_stats_section(self, user_id: str) -> None:
        """Render the monthly statistics section."""
        try:
            st.markdown("### 📅 月別統計")

            # Month selection interface
            col1, col2, col3 = st.columns(3)

            with col1:
                current_year = datetime.now().year
                selected_year = st.selectbox(
                    "年",
                    range(current_year - 2, current_year + 1),
                    index=2,
                    key="monthly_year"
                )

            with col2:
                current_month = datetime.now().month
                selected_month = st.selectbox(
                    "月",
                    range(1, 13),
                    index=current_month - 1,
                    key="monthly_month"
                )

            with col3:
                months_range = st.selectbox(
                    "表示期間",
                    [1, 3, 6, 12],
                    index=2,
                    key="monthly_range",
                    help="選択した月から過去何ヶ月分を表示するか"
                )

            # Calculate date range
            end_year = selected_year
            end_month = selected_month
            start_year = selected_year
            start_month = selected_month - months_range + 1

            if start_month <= 0:
                start_month += 12
                start_year -= 1

            # Get monthly statistics
            monthly_stats = self.stats_calculator.get_monthly_stats_range(
                user_id, start_year, start_month, end_year, end_month
            )

            if not monthly_stats:
                st.info("選択した期間にデータがありません。")
                return

            # Generate and display monthly chart
            monthly_chart = self.stats_calculator.generate_monthly_stats_chart(
                monthly_stats)
            st.plotly_chart(monthly_chart, use_container_width=True)

            # Display monthly summary table
            with st.expander("📋 月別詳細データ", expanded=False):
                self._render_monthly_stats_table(monthly_stats)

        except Exception as e:
            st.error("月別統計の表示中にエラーが発生しました。")
            self.logger.error(f"Error rendering monthly stats: {e}")

    def _render_monthly_stats_table(self, monthly_stats: List) -> None:
        """Render monthly statistics in a table format with colors."""
        if not monthly_stats:
            return

        # Display colored monthly stats
        for stats in monthly_stats:
            profit_class = self.get_profit_color_class(
                stats.basic_stats.total_profit)
            win_rate_class = self.get_win_rate_color_class(
                stats.basic_stats.win_rate)
            monthly_class = "monthly-profit" if stats.basic_stats.total_profit > 0 else "monthly-loss" if stats.basic_stats.total_profit < 0 else "monthly-neutral"

            st.markdown(f"""
            <div class="session-card {monthly_class}" style="margin: 8px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong style="color: #FFD700; font-size: 1.1em;">
                            {stats.year}/{stats.month:02d}
                        </strong>
                    </div>
                    <div style="flex: 3; text-align: right;">
                        <span style="margin: 0 8px;">セッション: {stats.basic_stats.completed_sessions}回</span>
                        <span class="{profit_class}" style="margin: 0 8px; font-weight: bold;">
                            総収支: {stats.basic_stats.total_profit:+,}円
                        </span>
                        <span class="{win_rate_class}" style="margin: 0 8px; font-weight: bold;">
                            勝率: {stats.basic_stats.win_rate:.1f}%
                        </span>
                        <span style="margin: 0 8px; color: #00BFFF;">
                            平均投資: {stats.basic_stats.avg_investment:,.0f}円
                        </span>
                        <span class="{profit_class}" style="margin: 0 8px;">
                            平均収支: {stats.basic_stats.avg_profit:+,.0f}円
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_machine_stats_section(self, user_id: str) -> None:
        """Render the machine statistics section."""
        try:
            st.markdown("### 🎰 機種別統計")

            # Get machine statistics
            machine_stats = self.stats_calculator.get_all_machine_stats(
                user_id)

            if not machine_stats:
                st.info("機種別データがありません。")
                return

            # Minimum sessions filter
            min_sessions = st.slider(
                "最低セッション数",
                min_value=1,
                max_value=10,
                value=3,
                key="machine_min_sessions",
                help="統計に含める最低セッション数を設定"
            )

            # Filter machines with sufficient data
            qualified_machines = [
                m for m in machine_stats
                if m.basic_stats.completed_sessions >= min_sessions
            ]

            if not qualified_machines:
                st.warning(
                    f"⚠️ 最低{min_sessions}セッション以上の機種がありません。フィルターを調整してください。")
                return

            # Generate and display machine chart
            machine_chart = self.stats_calculator.generate_machine_stats_chart(
                machine_stats, min_sessions
            )
            st.plotly_chart(machine_chart, use_container_width=True)

            # Display machine ranking
            with st.expander("🏆 機種別ランキング", expanded=False):
                self._render_machine_ranking_table(qualified_machines)

        except Exception as e:
            st.error("機種別統計の表示中にエラーが発生しました。")
            self.logger.error(f"Error rendering machine stats: {e}")

    def _render_machine_ranking_table(self, machine_stats: List) -> None:
        """Render machine ranking table."""
        if not machine_stats:
            return

        # Sort by total profit
        sorted_machines = sorted(
            machine_stats, key=lambda x: x.basic_stats.total_profit, reverse=True)

        # Display colored ranking table
        for i, stats in enumerate(sorted_machines[:10], 1):  # Top 10
            rank_class = self.get_ranking_class(i, len(sorted_machines))
            profit_class = self.get_profit_color_class(
                stats.basic_stats.total_profit)
            win_rate_class = self.get_win_rate_color_class(
                stats.basic_stats.win_rate)
            machine_class = self.get_machine_performance_class(
                stats.basic_stats.avg_profit, stats.basic_stats.completed_sessions)

            st.markdown(f"""
            <div class="session-card {machine_class}" style="margin: 5px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <span class="{rank_class}" style="font-size: 1.2em; padding: 5px 10px; border-radius: 15px; margin-right: 10px;">
                            #{i}
                        </span>
                        <strong>{stats.machine_name}</strong>
                    </div>
                    <div style="flex: 2; text-align: right;">
                        <span style="margin: 0 10px;">セッション: {stats.basic_stats.completed_sessions}回</span>
                        <span class="{profit_class}" style="margin: 0 10px; font-weight: bold;">
                            総収支: {stats.basic_stats.total_profit:+,}円
                        </span>
                        <span class="{win_rate_class}" style="margin: 0 10px; font-weight: bold;">
                            勝率: {stats.basic_stats.win_rate:.1f}%
                        </span>
                        <span class="{profit_class}" style="margin: 0 10px;">
                            平均: {stats.basic_stats.avg_profit:+,.0f}円
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_history_page(self) -> None:
        """Render the history page with session history and filtering."""
        st.markdown("## 📋 遊技履歴")

        # Render history filtering controls
        self._render_history_filters()

        # Add export button
        col1, col2, col3 = st.columns([2, 1, 1])
        with col3:
            self.render_export_options()

        # Render history list
        self._render_history_list()

    def _render_settings_page(self) -> None:
        """Render the settings page."""
        st.markdown("## ⚙️ 設定")
        st.info("設定機能は今後実装予定です")

    def apply_custom_styling(self) -> None:
        """Apply custom CSS styling to the Streamlit app."""
        # Load external CSS file
        try:
            import os
            css_file_path = os.path.join(os.path.dirname(
                os.path.dirname(__file__)), 'static', 'style.css')
            if os.path.exists(css_file_path):
                with open(css_file_path, 'r', encoding='utf-8') as f:
                    css_content = f.read()
                st.markdown(f"<style>{css_content}</style>",
                            unsafe_allow_html=True)
            else:
                self.logger.warning(f"CSS file not found: {css_file_path}")
        except Exception as e:
            self.logger.error(f"Error loading CSS file: {e}")

        # Additional inline CSS for button styling
        st.markdown("""
        <style>
        /* Enhanced button styling */
        .stButton > button {
            background: linear-gradient(45deg, #8A2BE2 0%, #00BFFF 50%, #FFD700 100%) !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 15px 30px !important;
            color: white !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 6px 20px rgba(138, 43, 226, 0.4),
                        0 3px 10px rgba(0, 191, 255, 0.3) !important;
            border: 2px solid rgba(255, 215, 0, 0.3) !important;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .stButton > button::before {
            content: '' !important;
            position: absolute !important;
            top: 0 !important;
            left: -100% !important;
            width: 100% !important;
            height: 100% !important;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent) !important;
            transition: left 0.5s !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) scale(1.05) !important;
            box-shadow: 0 10px 30px rgba(138, 43, 226, 0.6),
                        0 5px 15px rgba(0, 191, 255, 0.4),
                        0 0 20px rgba(255, 215, 0, 0.3) !important;
            border: 2px solid rgba(255, 215, 0, 0.8) !important;
        }
        
        .stButton > button:hover::before {
            left: 100% !important;
        }
        
        .stButton > button:active {
            transform: translateY(-1px) scale(1.02) !important;
            box-shadow: 0 5px 15px rgba(138, 43, 226, 0.5) !important;
        }
        
        /* Form submit button special styling */
        .stForm .stButton > button {
            background: linear-gradient(45deg, #FFD700 0%, #8A2BE2 50%, #00BFFF 100%) !important;
            font-size: 1.1em !important;
            padding: 18px 35px !important;
        }
        
        /* Navigation button styling */
        div[data-testid="column"] .stButton > button {
            font-size: 0.9em !important;
            padding: 12px 20px !important;
        }
        </style>
        """, unsafe_allow_html=True)

    def handle_responsive_layout(self) -> None:
        """Handle responsive layout adjustments based on screen size."""
        # Detect screen size using JavaScript and adjust layout accordingly
        st.markdown("""
        <script>
        function detectScreenSize() {
            const width = window.innerWidth;
            const height = window.innerHeight;
            const isMobile = width <= 768;
            const isTablet = width > 768 && width <= 1024;
            const isDesktop = width > 1024;
            
            // Store screen info in session storage for Python access
            sessionStorage.setItem('screenWidth', width);
            sessionStorage.setItem('screenHeight', height);
            sessionStorage.setItem('isMobile', isMobile);
            sessionStorage.setItem('isTablet', isTablet);
            sessionStorage.setItem('isDesktop', isDesktop);
            
            // Add CSS classes based on screen size
            document.body.classList.remove('mobile-layout', 'tablet-layout', 'desktop-layout');
            if (isMobile) {
                document.body.classList.add('mobile-layout');
            } else if (isTablet) {
                document.body.classList.add('tablet-layout');
            } else {
                document.body.classList.add('desktop-layout');
            }
        }
        
        // Run on load and resize
        detectScreenSize();
        window.addEventListener('resize', detectScreenSize);
        window.addEventListener('orientationchange', function() {
            setTimeout(detectScreenSize, 100);
        });
        </script>
        """, unsafe_allow_html=True)

        # Apply responsive CSS
        self._apply_responsive_css()

    def _apply_responsive_css(self) -> None:
        """Apply responsive CSS styles for different screen sizes."""
        st.markdown("""
        <style>
        /* Mobile-first responsive design */
        
        /* Mobile Layout (≤ 768px) */
        @media (max-width: 768px) {
            .mobile-layout .main-header {
                padding: 15px 10px !important;
                margin-bottom: 15px !important;
                border-radius: 10px !important;
            }
            
            .mobile-layout .main-header h1 {
                font-size: 1.8em !important;
                margin: 0 !important;
            }
            
            .mobile-layout .main-header p {
                font-size: 1em !important;
                margin: 5px 0 0 0 !important;
            }
            
            /* Mobile navigation - stack vertically */
            .mobile-layout div[data-testid="column"] {
                min-width: 100% !important;
                margin-bottom: 8px !important;
            }
            
            .mobile-layout .stButton > button {
                width: 100% !important;
                padding: 12px 15px !important;
                font-size: 0.9em !important;
                margin-bottom: 5px !important;
                border-radius: 15px !important;
            }
            
            /* Mobile stat cards */
            .mobile-layout .stat-card {
                padding: 15px !important;
                margin: 8px 0 !important;
                border-radius: 12px !important;
            }
            
            .mobile-layout .stat-card h3 {
                font-size: 1em !important;
                margin-bottom: 8px !important;
            }
            
            .mobile-layout .stat-card p {
                font-size: 1.5em !important;
            }
            
            /* Mobile session cards */
            .mobile-layout .session-card {
                padding: 12px !important;
                margin: 8px 0 !important;
                border-radius: 10px !important;
            }
            
            .mobile-layout .session-card h4 {
                font-size: 1.1em !important;
                margin-bottom: 8px !important;
            }
            
            /* Mobile form styling */
            .mobile-layout .form-container {
                padding: 15px !important;
                margin: 10px 0 !important;
                border-radius: 12px !important;
            }
            
            /* Touch-optimized input fields */
            .mobile-layout .stTextInput > div > div > input,
            .mobile-layout .stNumberInput > div > div > input,
            .mobile-layout .stSelectbox > div > div,
            .mobile-layout .stDateInput > div > div > input,
            .mobile-layout .stTimeInput > div > div > input {
                min-height: 44px !important;
                font-size: 16px !important;
                padding: 12px 15px !important;
                border-radius: 12px !important;
            }
            
            /* Mobile metric containers */
            .mobile-layout .metric-container {
                padding: 12px !important;
                margin: 8px 0 !important;
                border-radius: 10px !important;
            }
            
            /* Mobile tabs */
            .mobile-layout .stTabs [data-baseweb="tab"] {
                padding: 10px 8px !important;
                font-size: 0.9em !important;
            }
            
            /* Mobile expanders */
            .mobile-layout .streamlit-expanderHeader {
                padding: 12px !important;
                font-size: 1em !important;
            }
            
            .mobile-layout .streamlit-expanderContent {
                padding: 12px !important;
            }
            
            /* Hide complex animations on mobile for performance */
            .mobile-layout * {
                animation-duration: 0.2s !important;
            }
            
            /* Mobile-specific touch targets */
            .mobile-layout .stButton > button:hover {
                transform: scale(1.02) !important;
            }
            
            .mobile-layout .stButton > button:active {
                transform: scale(0.98) !important;
                transition: transform 0.1s !important;
            }
        }
        
        /* Tablet Layout (769px - 1024px) */
        @media (min-width: 769px) and (max-width: 1024px) {
            .tablet-layout .main-header {
                padding: 20px 15px !important;
                margin-bottom: 20px !important;
            }
            
            .tablet-layout .main-header h1 {
                font-size: 2.2em !important;
            }
            
            .tablet-layout .main-header p {
                font-size: 1.1em !important;
            }
            
            /* Tablet navigation - 2-3 columns */
            .tablet-layout div[data-testid="column"] {
                min-width: 48% !important;
                margin: 0 1% 10px 1% !important;
            }
            
            .tablet-layout .stButton > button {
                padding: 14px 20px !important;
                font-size: 1em !important;
            }
            
            /* Tablet stat cards - 2 columns */
            .tablet-layout .stat-card {
                padding: 18px !important;
                margin: 10px 0 !important;
            }
            
            /* Tablet form styling */
            .tablet-layout .form-container {
                padding: 20px !important;
                margin: 15px 0 !important;
            }
            
            /* Touch-friendly inputs for tablet */
            .tablet-layout .stTextInput > div > div > input,
            .tablet-layout .stNumberInput > div > div > input,
            .tablet-layout .stSelectbox > div > div,
            .tablet-layout .stDateInput > div > div > input,
            .tablet-layout .stTimeInput > div > div > input {
                min-height: 40px !important;
                font-size: 15px !important;
                padding: 10px 12px !important;
            }
        }
        
        /* Desktop Layout (> 1024px) */
        @media (min-width: 1025px) {
            .desktop-layout .main-header {
                padding: 30px 20px !important;
                margin-bottom: 30px !important;
            }
            
            .desktop-layout .main-header h1 {
                font-size: 2.5em !important;
            }
            
            .desktop-layout .main-header p {
                font-size: 1.2em !important;
            }
            
            /* Desktop navigation - full row */
            .desktop-layout div[data-testid="column"] {
                margin: 0 5px !important;
            }
            
            .desktop-layout .stButton > button {
                padding: 15px 30px !important;
                font-size: 1em !important;
            }
            
            /* Desktop stat cards - 3 columns */
            .desktop-layout .stat-card {
                padding: 25px !important;
                margin: 15px 0 !important;
            }
            
            /* Desktop form styling */
            .desktop-layout .form-container {
                padding: 25px !important;
                margin: 20px 0 !important;
            }
            
            /* Desktop hover effects */
            .desktop-layout .stButton > button:hover {
                transform: translateY(-3px) scale(1.05) !important;
            }
            
            .desktop-layout .stat-card:hover {
                transform: translateY(-5px) scale(1.02) !important;
            }
        }
        
        /* Orientation-specific styles */
        @media (orientation: landscape) and (max-width: 1024px) {
            .main-header h1 {
                font-size: 2em !important;
            }
            
            .main-header p {
                font-size: 1em !important;
            }
            
            /* Landscape mobile/tablet - horizontal navigation */
            div[data-testid="column"] {
                min-width: auto !important;
                margin: 0 2px !important;
            }
            
            .stButton > button {
                padding: 10px 15px !important;
                font-size: 0.9em !important;
            }
        }
        
        /* High DPI displays */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
            .main-header {
                border-width: 2px !important;
            }
            
            .stat-card, .session-card {
                border-width: 1.5px !important;
            }
        }
        
        /* Accessibility - Reduce motion */
        @media (prefers-reduced-motion: reduce) {
            .mobile-layout *, .tablet-layout *, .desktop-layout * {
                animation: none !important;
                transition: none !important;
            }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background: linear-gradient(135deg, #0a0a1a 0%, #0f1419 50%, #0a1a2e 100%) !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def apply_data_update_animation(self, element_key: str) -> None:
        """Apply fade animation for data updates."""
        # Add CSS class for data update animation
        st.markdown(f"""
        <script>
        setTimeout(function() {{
            const element = document.querySelector('[data-testid="{element_key}"]');
            if (element) {{
                element.classList.add('data-update-fade');
                setTimeout(function() {{
                    element.classList.remove('data-update-fade');
                }}, 800);
            }}
        }}, 100);
        </script>
        """, unsafe_allow_html=True)

    def show_loading_spinner(self, message: str = "読み込み中...") -> None:
        """Show loading spinner with animation."""
        st.markdown(f"""
        <div style="text-align: center; padding: 20px;">
            <div class="loading-spinner"></div>
            <p style="color: #FFD700; margin-top: 10px; font-weight: bold;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

    def animate_metric_update(self, label: str, value: str, delta: str = None) -> None:
        """Display metric with update animation."""
        delta_html = f'<p style="font-size: 0.8em; color: #00BFFF; margin: 5px 0;">{delta}</p>' if delta else ''

        st.markdown(f"""
        <div class="metric-container metric-value-update">
            <h4 style="color: #FFD700; margin: 0 0 10px 0;">{label}</h4>
            <p style="font-size: 2em; font-weight: bold; color: #FFFFFF; margin: 0;">{value}</p>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

    def show_animated_success(self, message: str) -> None:
        """Show success message with enhanced animation."""
        st.markdown(f"""
        <div class="stSuccess" style="animation: fadeIn 0.5s ease, pulse 2s infinite, glow 2s infinite;">
            <p style="margin: 0; font-weight: bold; text-align: center;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

    def show_animated_error(self, message: str) -> None:
        """Show error message with enhanced animation."""
        st.markdown(f"""
        <div class="stError" style="animation: fadeIn 0.5s ease, pulse 2s infinite;">
            <p style="margin: 0; font-weight: bold; text-align: center;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

    def get_profit_color_class(self, profit: float) -> str:
        """
        Get the appropriate CSS class for profit display based on value.

        Args:
            profit: The profit value

        Returns:
            str: CSS class name for profit display
        """
        if profit > 0:
            return "profit-positive"
        elif profit < 0:
            return "profit-negative"
        else:
            return "profit-neutral"

    def get_profit_bg_class(self, profit: float) -> str:
        """
        Get the appropriate background CSS class for profit display.

        Args:
            profit: The profit value

        Returns:
            str: CSS class name for profit background
        """
        if profit > 0:
            return "profit-positive-bg"
        elif profit < 0:
            return "profit-negative-bg"
        else:
            return "profit-neutral-bg"

    def get_win_rate_color_class(self, win_rate: float) -> str:
        """
        Get the appropriate CSS class for win rate display.

        Args:
            win_rate: Win rate percentage (0-100)

        Returns:
            str: CSS class name for win rate display
        """
        if win_rate >= 70:
            return "win-rate-excellent"
        elif win_rate >= 60:
            return "win-rate-good"
        elif win_rate >= 50:
            return "win-rate-average"
        elif win_rate >= 40:
            return "win-rate-poor"
        else:
            return "win-rate-bad"

    def get_session_status_class(self, profit: float) -> str:
        """
        Get the appropriate CSS class for session status display.

        Args:
            profit: Session profit value

        Returns:
            str: CSS class name for session status
        """
        if profit > 0:
            return "session-winning"
        elif profit < 0:
            return "session-losing"
        else:
            return "session-neutral"

    def get_machine_performance_class(self, avg_profit: float, sessions: int) -> str:
        """
        Get the appropriate CSS class for machine performance display.

        Args:
            avg_profit: Average profit per session
            sessions: Number of sessions

        Returns:
            str: CSS class name for machine performance
        """
        if sessions < 3:
            return "machine-average"  # Not enough data

        if avg_profit >= 5000:
            return "machine-excellent"
        elif avg_profit >= 1000:
            return "machine-good"
        elif avg_profit >= -1000:
            return "machine-average"
        elif avg_profit >= -5000:
            return "machine-poor"
        else:
            return "machine-bad"

    def get_investment_level_class(self, investment: int) -> str:
        """
        Get the appropriate CSS class for investment amount display.

        Args:
            investment: Investment amount

        Returns:
            str: CSS class name for investment level
        """
        if investment >= 30000:
            return "investment-high"
        elif investment >= 15000:
            return "investment-medium"
        else:
            return "investment-low"

    def get_ranking_class(self, rank: int, total: int) -> str:
        """
        Get the appropriate CSS class for ranking display.

        Args:
            rank: Current rank (1-based)
            total: Total number of items

        Returns:
            str: CSS class name for ranking
        """
        if rank == 1:
            return "rank-1"
        elif rank == 2:
            return "rank-2"
        elif rank == 3:
            return "rank-3"
        elif rank <= total * 0.2:  # Top 20%
            return "rank-top"
        elif rank >= total * 0.8:  # Bottom 20%
            return "rank-bottom"
        else:
            return ""

    def render_colored_profit(self, profit: float, size: str = "1.5em", show_background: bool = False) -> None:
        """
        Render profit value with appropriate colors and animations.

        Args:
            profit: Profit value to display
            size: Font size for the display
            show_background: Whether to show colored background
        """
        profit_class = self.get_profit_color_class(profit)
        bg_class = self.get_profit_bg_class(profit) if show_background else ""

        st.markdown(f"""
        <div class="{bg_class}" style="padding: 10px; border-radius: 10px; text-align: center; margin: 5px 0;">
            <p class="{profit_class}" style="font-size: {size}; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
                {profit:+,}円
            </p>
        </div>
        """, unsafe_allow_html=True)

    def render_colored_win_rate(self, win_rate: float, size: str = "1.2em") -> None:
        """
        Render win rate with appropriate colors.

        Args:
            win_rate: Win rate percentage
            size: Font size for the display
        """
        win_rate_class = self.get_win_rate_color_class(win_rate)

        st.markdown(f"""
        <p class="{win_rate_class}" style="font-size: {size}; margin: 0; text-align: center;">
            {win_rate:.1f}%
        </p>
        """, unsafe_allow_html=True)

    def validate_browser_compatibility(self) -> bool:
        """Validate browser compatibility and show warnings if needed."""
        st.markdown("""
        <script>
        function checkBrowserCompatibility() {
            const isIE = /MSIE|Trident/.test(navigator.userAgent);
            const isOldChrome = /Chrome\/([0-9]+)/.test(navigator.userAgent) && 
                               parseInt(navigator.userAgent.match(/Chrome\/([0-9]+)/)[1]) < 60;
            const isOldFirefox = /Firefox\/([0-9]+)/.test(navigator.userAgent) && 
                                parseInt(navigator.userAgent.match(/Firefox\/([0-9]+)/)[1]) < 60;
            const isOldSafari = /Safari\/([0-9]+)/.test(navigator.userAgent) && 
                               parseInt(navigator.userAgent.match(/Safari\/([0-9]+)/)[1]) < 600;
            
            if (isIE || isOldChrome || isOldFirefox || isOldSafari) {
                sessionStorage.setItem('browserCompatible', 'false');
                return false;
            }
            
            sessionStorage.setItem('browserCompatible', 'true');
            return true;
        }
        
        checkBrowserCompatibility();
        </script>
        """, unsafe_allow_html=True)
        return True

    def optimize_for_touch(self) -> None:
        """Optimize UI elements for touch interaction on mobile devices."""
        st.markdown("""
        <style>
        /* Touch optimization styles */
        .touch-optimized {
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            -webkit-tap-highlight-color: rgba(255, 215, 0, 0.3);
        }
        
        /* Touch-friendly button sizing */
        .stButton > button {
            min-height: 44px !important;
            min-width: 44px !important;
            touch-action: manipulation !important;
        }
        
        /* Touch-friendly input fields */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div,
        .stDateInput > div > div > input,
        .stTimeInput > div > div > input {
            min-height: 44px !important;
            touch-action: manipulation !important;
        }
        
        /* Touch feedback for interactive elements */
        .stButton > button:active,
        .stat-card:active,
        .session-card:active {
            background-color: rgba(255, 215, 0, 0.1) !important;
            transform: scale(0.98) !important;
            transition: all 0.1s ease !important;
        }
        
        /* Prevent zoom on input focus (iOS) */
        @media screen and (-webkit-min-device-pixel-ratio: 0) {
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input,
            .stSelectbox > div > div select {
                font-size: 16px !important;
            }
        }
        
        /* Swipe gesture support */
        .swipeable {
            touch-action: pan-x pan-y !important;
        }
        
        /* Improved scrolling on mobile */
        .stApp {
            -webkit-overflow-scrolling: touch !important;
            overflow-scrolling: touch !important;
        }
        
        /* Touch-friendly tabs */
        .stTabs [data-baseweb="tab"] {
            min-height: 44px !important;
            padding: 12px 16px !important;
            touch-action: manipulation !important;
        }
        
        /* Touch-friendly expanders */
        .streamlit-expanderHeader {
            min-height: 44px !important;
            touch-action: manipulation !important;
        }
        
        /* Prevent text selection on UI elements */
        .main-header, .stat-card h3, .session-card h4 {
            -webkit-user-select: none !important;
            -moz-user-select: none !important;
            -ms-user-select: none !important;
            user-select: none !important;
        }
        </style>
        """, unsafe_allow_html=True)

    def handle_orientation_change(self) -> None:
        """Handle device orientation changes and adjust layout accordingly."""
        st.markdown("""
        <script>
        function handleOrientationChange() {
            const orientation = window.orientation || (window.innerWidth > window.innerHeight ? 90 : 0);
            const isLandscape = Math.abs(orientation) === 90;
            
            // Store orientation info
            sessionStorage.setItem('isLandscape', isLandscape);
            sessionStorage.setItem('orientation', orientation);
            
            // Add orientation classes
            document.body.classList.remove('portrait-mode', 'landscape-mode');
            if (isLandscape) {
                document.body.classList.add('landscape-mode');
            } else {
                document.body.classList.add('portrait-mode');
            }
            
            // Trigger layout recalculation
            window.dispatchEvent(new Event('resize'));
        }
        
        // Handle orientation change
        window.addEventListener('orientationchange', function() {
            setTimeout(handleOrientationChange, 100);
        });
        
        // Initial orientation setup
        handleOrientationChange();
        </script>
        """, unsafe_allow_html=True)

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information for responsive design decisions."""
        # This would typically use JavaScript to get real device info
        # For now, return default values that can be overridden
        return {
            'is_mobile': False,
            'is_tablet': False,
            'is_desktop': True,
            'screen_width': 1920,
            'screen_height': 1080,
            'is_landscape': True,
            'is_touch_device': False,
            'pixel_ratio': 1.0
        }

    def optimize_for_desktop(self) -> None:
        """Optimize UI layout for desktop/large screen displays."""
        st.markdown("""
        <style>
        /* Desktop-specific optimizations */
        @media (min-width: 1025px) {
            /* Large screen layout improvements */
            .desktop-layout .main-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 0 20px;
            }
            
            /* Desktop navigation - enhanced spacing */
            .desktop-layout div[data-testid="column"] {
                margin: 0 8px !important;
                padding: 0 4px !important;
            }
            
            .desktop-layout .stButton > button {
                padding: 16px 32px !important;
                font-size: 1.1em !important;
                min-width: 120px !important;
                border-radius: 25px !important;
            }
            
            /* Desktop stat cards - enhanced 3-column layout */
            .desktop-layout .stat-card {
                padding: 30px 25px !important;
                margin: 20px 0 !important;
                border-radius: 20px !important;
                min-height: 150px !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
            }
            
            .desktop-layout .stat-card h3 {
                font-size: 1.3em !important;
                margin-bottom: 15px !important;
            }
            
            .desktop-layout .stat-card p {
                font-size: 2.2em !important;
                margin: 0 !important;
            }
            
            /* Desktop session cards - enhanced layout */
            .desktop-layout .session-card {
                padding: 25px 30px !important;
                margin: 15px 0 !important;
                border-radius: 18px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
            }
            
            .desktop-layout .session-card h4 {
                font-size: 1.4em !important;
                margin: 0 0 10px 0 !important;
                flex: 1 !important;
            }
            
            .desktop-layout .session-card .session-details {
                flex: 2 !important;
                text-align: right !important;
            }
            
            /* Desktop form containers - side-by-side layout */
            .desktop-layout .form-container {
                padding: 30px 35px !important;
                margin: 25px 0 !important;
                border-radius: 25px !important;
            }
            
            /* Desktop input fields - enhanced styling */
            .desktop-layout .stTextInput > div > div > input,
            .desktop-layout .stNumberInput > div > div > input,
            .desktop-layout .stSelectbox > div > div,
            .desktop-layout .stDateInput > div > div > input,
            .desktop-layout .stTimeInput > div > div > input {
                min-height: 48px !important;
                font-size: 16px !important;
                padding: 12px 18px !important;
                border-radius: 18px !important;
            }
            
            /* Desktop tabs - enhanced styling */
            .desktop-layout .stTabs [data-baseweb="tab"] {
                padding: 15px 25px !important;
                font-size: 1.1em !important;
                min-width: 120px !important;
                border-radius: 15px !important;
            }
            
            /* Desktop metrics - enhanced layout */
            .desktop-layout .metric-container {
                padding: 25px 30px !important;
                margin: 15px 0 !important;
                border-radius: 18px !important;
                min-height: 120px !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
            }
            
            /* Desktop expanders - enhanced styling */
            .desktop-layout .streamlit-expanderHeader {
                padding: 18px 25px !important;
                font-size: 1.2em !important;
                border-radius: 18px !important;
            }
            
            .desktop-layout .streamlit-expanderContent {
                padding: 25px 30px !important;
                border-radius: 0 0 18px 18px !important;
            }
            
            /* Desktop hover effects - enhanced */
            .desktop-layout .stButton > button:hover {
                transform: translateY(-4px) scale(1.08) !important;
                box-shadow: 0 12px 35px rgba(138, 43, 226, 0.6),
                           0 6px 20px rgba(0, 191, 255, 0.4),
                           0 0 25px rgba(255, 215, 0, 0.3) !important;
            }
            
            .desktop-layout .stat-card:hover {
                transform: translateY(-6px) scale(1.03) !important;
                box-shadow: 0 15px 40px rgba(138, 43, 226, 0.5),
                           0 8px 25px rgba(0, 191, 255, 0.3) !important;
            }
            
            .desktop-layout .session-card:hover {
                transform: translateY(-4px) scale(1.02) !important;
                box-shadow: 0 12px 30px rgba(138, 43, 226, 0.4) !important;
            }
            
            /* Desktop sidebar enhancements */
            .desktop-layout .css-1d391kg {
                width: 300px !important;
                padding: 20px !important;
            }
            
            /* Desktop chart containers - larger sizing */
            .desktop-layout .js-plotly-plot {
                min-height: 400px !important;
            }
            
            /* Desktop dataframe styling */
            .desktop-layout .stDataFrame {
                border-radius: 20px !important;
                overflow: hidden !important;
            }
            
            /* Desktop multi-column layouts */
            .desktop-layout .desktop-multi-column {
                display: grid !important;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
                gap: 20px !important;
                margin: 20px 0 !important;
            }
            
            /* Desktop dashboard grid */
            .desktop-layout .dashboard-grid {
                display: grid !important;
                grid-template-columns: 1fr 1fr 1fr !important;
                gap: 25px !important;
                margin: 25px 0 !important;
            }
            
            /* Desktop stats grid */
            .desktop-layout .stats-grid {
                display: grid !important;
                grid-template-columns: 2fr 1fr !important;
                gap: 30px !important;
                margin: 30px 0 !important;
            }
        }
        
        /* Ultra-wide screen optimizations (> 1440px) */
        @media (min-width: 1441px) {
            .desktop-layout .main-container {
                max-width: 1600px !important;
            }
            
            .desktop-layout .dashboard-grid {
                grid-template-columns: 1fr 1fr 1fr 1fr !important;
            }
            
            .desktop-layout .stats-grid {
                grid-template-columns: 3fr 1fr !important;
            }
        }
        
        /* 4K display optimizations (> 2560px) */
        @media (min-width: 2561px) {
            .desktop-layout .main-container {
                max-width: 2000px !important;
            }
            
            .desktop-layout .stApp {
                font-size: 18px !important;
            }
            
            .desktop-layout .main-header h1 {
                font-size: 3em !important;
            }
            
            .desktop-layout .stat-card {
                min-height: 200px !important;
                padding: 40px 35px !important;
            }
            
            .desktop-layout .stat-card p {
                font-size: 2.8em !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def handle_multi_tab_consistency(self) -> None:
        """Handle data consistency across multiple browser tabs."""
        st.markdown("""
        <script>
        // Multi-tab data synchronization
        class MultiTabSync {
            constructor() {
                this.storageKey = 'pachinko_app_data';
                this.lastUpdateKey = 'pachinko_app_last_update';
                this.tabId = 'tab_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                
                // Listen for storage changes from other tabs
                window.addEventListener('storage', this.handleStorageChange.bind(this));
                
                // Listen for beforeunload to clean up
                window.addEventListener('beforeunload', this.cleanup.bind(this));
                
                // Periodic sync check
                this.syncInterval = setInterval(this.checkForUpdates.bind(this), 1000);
                
                // Register this tab
                this.registerTab();
            }
            
            registerTab() {
                const activeTabs = JSON.parse(localStorage.getItem('active_tabs') || '[]');
                if (!activeTabs.includes(this.tabId)) {
                    activeTabs.push(this.tabId);
                    localStorage.setItem('active_tabs', JSON.stringify(activeTabs));
                }
            }
            
            handleStorageChange(event) {
                if (event.key === this.storageKey) {
                    // Data was updated in another tab
                    this.notifyDataUpdate();
                } else if (event.key === this.lastUpdateKey) {
                    // Check if we need to refresh
                    const lastUpdate = parseInt(event.newValue || '0');
                    const ourLastUpdate = parseInt(sessionStorage.getItem('our_last_update') || '0');
                    
                    if (lastUpdate > ourLastUpdate) {
                        this.showSyncNotification();
                    }
                }
            }
            
            notifyDataUpdate() {
                // Show notification that data was updated in another tab
                const notification = document.createElement('div');
                notification.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 20px;
                        right: 20px;
                        background: linear-gradient(135deg, #8A2BE2, #00BFFF);
                        color: white;
                        padding: 15px 20px;
                        border-radius: 15px;
                        box-shadow: 0 8px 25px rgba(138, 43, 226, 0.4);
                        z-index: 9999;
                        font-weight: bold;
                        border: 2px solid rgba(255, 215, 0, 0.5);
                    ">
                        📊 データが他のタブで更新されました
                        <button onclick="location.reload()" style="
                            background: #FFD700;
                            color: #000;
                            border: none;
                            padding: 5px 10px;
                            border-radius: 10px;
                            margin-left: 10px;
                            cursor: pointer;
                            font-weight: bold;
                        ">更新</button>
                        <button onclick="this.parentElement.parentElement.remove()" style="
                            background: transparent;
                            color: white;
                            border: 1px solid white;
                            padding: 5px 10px;
                            border-radius: 10px;
                            margin-left: 5px;
                            cursor: pointer;
                        ">閉じる</button>
                    </div>
                `;
                document.body.appendChild(notification);
                
                // Auto-remove after 10 seconds
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.parentElement.removeChild(notification);
                    }
                }, 10000);
            }
            
            showSyncNotification() {
                // Show a less intrusive sync notification
                const syncBar = document.createElement('div');
                syncBar.innerHTML = `
                    <div style="
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        background: linear-gradient(135deg, #FFD700, #8A2BE2);
                        color: white;
                        padding: 10px;
                        text-align: center;
                        z-index: 9998;
                        font-weight: bold;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
                    ">
                        🔄 他のタブでデータが更新されています
                        <button onclick="location.reload()" style="
                            background: white;
                            color: #8A2BE2;
                            border: none;
                            padding: 5px 15px;
                            border-radius: 15px;
                            margin-left: 15px;
                            cursor: pointer;
                            font-weight: bold;
                        ">同期</button>
                        <button onclick="this.parentElement.parentElement.remove()" style="
                            background: transparent;
                            color: white;
                            border: 1px solid white;
                            padding: 5px 15px;
                            border-radius: 15px;
                            margin-left: 10px;
                            cursor: pointer;
                        ">無視</button>
                    </div>
                `;
                document.body.appendChild(syncBar);
                
                // Auto-remove after 15 seconds
                setTimeout(() => {
                    if (syncBar.parentElement) {
                        syncBar.parentElement.removeChild(syncBar);
                    }
                }, 15000);
            }
            
            updateData(data) {
                // Update data and notify other tabs
                localStorage.setItem(this.storageKey, JSON.stringify(data));
                localStorage.setItem(this.lastUpdateKey, Date.now().toString());
                sessionStorage.setItem('our_last_update', Date.now().toString());
            }
            
            checkForUpdates() {
                // Periodic check for data consistency
                const lastUpdate = parseInt(localStorage.getItem(this.lastUpdateKey) || '0');
                const ourLastUpdate = parseInt(sessionStorage.getItem('our_last_update') || '0');
                
                if (lastUpdate > ourLastUpdate + 5000) { // 5 second threshold
                    this.showSyncNotification();
                }
            }
            
            cleanup() {
                // Clean up when tab is closed
                clearInterval(this.syncInterval);
                
                const activeTabs = JSON.parse(localStorage.getItem('active_tabs') || '[]');
                const updatedTabs = activeTabs.filter(id => id !== this.tabId);
                localStorage.setItem('active_tabs', JSON.stringify(updatedTabs));
            }
        }
        
        // Initialize multi-tab sync
        if (typeof window.multiTabSync === 'undefined') {
            window.multiTabSync = new MultiTabSync();
        }
        
        // Expose sync function for Streamlit to use
        window.syncData = function(data) {
            if (window.multiTabSync) {
                window.multiTabSync.updateData(data);
            }
        };
        
        // Check for tab conflicts on load
        window.addEventListener('load', function() {
            const activeTabs = JSON.parse(localStorage.getItem('active_tabs') || '[]');
            if (activeTabs.length > 1) {
                console.log('Multiple tabs detected:', activeTabs.length);
            }
        });
        </script>
        """, unsafe_allow_html=True)

    def render_desktop_dashboard(self) -> None:
        """Render an enhanced dashboard layout optimized for desktop screens."""
        # Add desktop-specific container
        st.markdown('<div class="desktop-layout main-container">',
                    unsafe_allow_html=True)

        try:
            user_id = st.session_state.user_id
            recent_sessions = self.db_manager.get_sessions_as_dict(
                user_id, limit=20)

            if recent_sessions:
                # Desktop dashboard grid
                st.markdown('<div class="dashboard-grid">',
                            unsafe_allow_html=True)

                # Calculate enhanced stats for desktop
                total_profit = sum(session.get('profit', 0)
                                   or 0 for session in recent_sessions)
                completed_sessions = len(
                    [s for s in recent_sessions if s.get('is_completed')])
                winning_sessions = len(
                    [s for s in recent_sessions if (s.get('profit', 0) or 0) > 0])
                win_rate = (winning_sessions / completed_sessions *
                            100) if completed_sessions > 0 else 0

                # Enhanced stat cards for desktop
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    profit_class = self.get_profit_color_class(total_profit)
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>💰 総収支</h3>
                        <p class="{profit_class}" style="font-size: 2.2em; font-weight: bold;">
                            {total_profit:+,}円
                        </p>
                        <small style="color: #B0B0B0;">最近20セッション</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    win_rate_class = self.get_win_rate_color_class(win_rate)
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>🎯 勝率</h3>
                        <p class="{win_rate_class}" style="font-size: 2.2em; font-weight: bold;">
                            {win_rate:.1f}%
                        </p>
                        <small style="color: #B0B0B0;">{winning_sessions}/{completed_sessions}勝</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>📊 完了セッション</h3>
                        <p style="font-size: 2.2em; font-weight: bold; color: #00BFFF;">
                            {completed_sessions}回
                        </p>
                        <small style="color: #B0B0B0;">総{len(recent_sessions)}セッション</small>
                    </div>
                    """, unsafe_allow_html=True)

                with col4:
                    avg_profit = total_profit / completed_sessions if completed_sessions > 0 else 0
                    avg_profit_class = self.get_profit_color_class(avg_profit)
                    st.markdown(f"""
                    <div class="stat-card">
                        <h3>📈 平均収支</h3>
                        <p class="{avg_profit_class}" style="font-size: 2.2em; font-weight: bold;">
                            {avg_profit:+,.0f}円
                        </p>
                        <small style="color: #B0B0B0;">1セッション当たり</small>
                    </div>
                    """, unsafe_allow_html=True)

                # Close dashboard-grid
                st.markdown('</div>', unsafe_allow_html=True)

                # Desktop-specific quick actions
                st.markdown("---")
                st.markdown("## 🚀 クイックアクション")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("🎮 新しい遊技開始", key="desktop_quick_start", use_container_width=True):
                        st.session_state.current_page = 'record'
                        st.rerun()

                with col2:
                    if st.button("📊 詳細統計", key="desktop_quick_stats", use_container_width=True):
                        st.session_state.current_page = 'stats'
                        st.rerun()

                with col3:
                    if st.button("📋 履歴確認", key="desktop_quick_history", use_container_width=True):
                        st.session_state.current_page = 'history'
                        st.rerun()

                with col4:
                    if st.button("💾 データエクスポート", key="desktop_quick_export", use_container_width=True):
                        st.info("エクスポート機能は今後実装予定です")

            else:
                st.info("まだ遊技記録がありません。「遊技記録」から始めましょう！")

        except Exception as e:
            st.error(f"ダッシュボードの表示中にエラーが発生しました: {e}")
            self.logger.error(f"Error in desktop dashboard: {e}")

        st.markdown('</div>', unsafe_allow_html=True)  # Close main-container

    def _render_session_start_form(self) -> None:
        """Render the form for starting a new gaming session."""
        st.markdown("### 🎯 新しい遊技を開始")

        with st.form("session_start_form"):
            col1, col2 = st.columns(2)

            with col1:
                # Date input
                session_date = st.date_input(
                    "遊技日",
                    value=date.today(),
                    max_value=date.today(),
                    help="遊技を行った日付を選択してください"
                )

                # Store name input
                store_name = st.text_input(
                    "店舗名",
                    placeholder="例: マルハン新宿店",
                    help="遊技した店舗名を入力してください"
                )

                # Initial investment
                initial_investment = st.number_input(
                    "開始投資額（円）",
                    min_value=0,
                    max_value=1000000,
                    value=10000,
                    step=1000,
                    help="遊技開始時の投資金額を入力してください"
                )

            with col2:
                # Start time input
                start_time = st.time_input(
                    "開始時間",
                    value=datetime.now().time(),
                    help="遊技を開始した時間を選択してください"
                )

                # Machine name input
                machine_name = st.text_input(
                    "機種名",
                    placeholder="例: CRフィーバー戦姫絶唱シンフォギア",
                    help="遊技した機種名を入力してください"
                )

            # Submit button
            submitted = st.form_submit_button(
                "🎮 遊技開始",
                use_container_width=True
            )

            if submitted:
                self._handle_session_start(
                    session_date, start_time, store_name,
                    machine_name, initial_investment
                )

    def _render_session_end_form(self, session_data: Dict[str, Any]) -> None:
        """Render the form for ending a gaming session."""
        st.markdown("### 🏁 遊技終了")

        # Display current session info
        st.markdown(f"""
        <div class="stat-card">
            <h3>現在の遊技情報</h3>
            <p><strong>店舗:</strong> {session_data['store_name']}</p>
            <p><strong>機種:</strong> {session_data['machine_name']}</p>
            <p><strong>開始投資額:</strong> {session_data['initial_investment']:,}円</p>
            <p><strong>開始時間:</strong> {session_data['start_time']}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("session_end_form"):
            col1, col2 = st.columns(2)

            with col1:
                # End time input
                end_time = st.time_input(
                    "終了時間",
                    value=datetime.now().time(),
                    help="遊技を終了した時間を選択してください"
                )

                # Final investment
                final_investment = st.number_input(
                    "最終投資額（円）",
                    min_value=session_data['initial_investment'],
                    max_value=1000000,
                    value=session_data['initial_investment'],
                    step=1000,
                    help="遊技終了時の総投資金額を入力してください"
                )

            with col2:
                # Return amount
                return_amount = st.number_input(
                    "回収金額（円）",
                    min_value=0,
                    max_value=10000000,
                    value=0,
                    step=1000,
                    help="遊技終了時の回収金額を入力してください"
                )

                # Real-time profit calculation with animation and colors
                profit = return_amount - final_investment
                profit_class = self.get_profit_color_class(profit)
                bg_class = self.get_profit_bg_class(profit)

                st.markdown(f"""
                <div class="{bg_class}" style="padding: 15px; border-radius: 15px; 
                           text-align: center; margin-top: 20px;">
                    <h4 style="color: #FFD700; margin: 0 0 10px 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">収支</h4>
                    <p class="{profit_class}" style="font-size: 1.8em; font-weight: bold; margin: 0;">
                        {profit:+,}円
                    </p>
                </div>
                """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                # Submit button
                submitted = st.form_submit_button(
                    "✅ 遊技終了",
                    use_container_width=True
                )

            with col2:
                # Cancel button
                cancelled = st.form_submit_button(
                    "❌ キャンセル",
                    use_container_width=True
                )

            if submitted:
                self._handle_session_end(
                    session_data['id'], end_time, final_investment, return_amount
                )

            if cancelled:
                st.session_state.active_session = None
                st.rerun()

    def _handle_session_start(self, session_date: date, start_time: time,
                              store_name: str, machine_name: str,
                              initial_investment: int) -> None:
        """Handle the session start form submission."""
        try:
            # Clear previous errors
            self.clear_form_errors()

            # Validate input data
            validation_errors = self.validate_session_start_input(
                session_date, start_time, store_name, machine_name, initial_investment
            )

            if validation_errors:
                st.session_state.form_errors = validation_errors
                self.display_validation_errors(validation_errors)
                return

            # Combine date and time
            start_datetime = datetime.combine(session_date, start_time)

            # Create GameSession object
            session = GameSession(
                user_id=st.session_state.user_id,
                date=datetime.combine(session_date, datetime.min.time()),
                start_time=start_datetime,
                store_name=store_name.strip(),
                machine_name=machine_name.strip(),
                initial_investment=initial_investment
            )

            # Save to database
            session_id = self.db_manager.create_session(session.to_dict())

            # Store active session in session state
            session_data = session.to_dict()
            session_data['id'] = session_id
            st.session_state.active_session = session_data

            self.show_validation_success("遊技を開始しました！終了時に結果を入力してください。")
            st.rerun()

        except ValidationError as e:
            st.error(f"入力エラー: {e.message}")
            st.session_state.form_errors[e.field_name] = e.message

        except DatabaseError as e:
            st.error(f"データベースエラー: {e}")
            self.logger.error(f"Database error in session start: {e}")

        except Exception as e:
            st.error("予期しないエラーが発生しました。")
            self.logger.error(f"Unexpected error in session start: {e}")

    def _handle_session_end(self, session_id: int, end_time: time,
                            final_investment: int, return_amount: int) -> None:
        """Handle the session end form submission."""
        try:
            # Clear previous errors
            self.clear_form_errors()

            # Get current session data
            session_data = st.session_state.active_session

            # Validate input data
            validation_errors = self.validate_session_end_input(
                session_data, end_time, final_investment, return_amount
            )

            if validation_errors:
                st.session_state.form_errors = validation_errors
                self.display_validation_errors(validation_errors)
                return

            start_datetime = datetime.fromisoformat(session_data['start_time'])

            # Combine date and time for end_time
            end_datetime = datetime.combine(start_datetime.date(), end_time)

            # Update session in database
            update_data = {
                'end_time': end_datetime.isoformat(),
                'final_investment': final_investment,
                'return_amount': return_amount,
                'profit': return_amount - final_investment,
                'is_completed': True,
                'updated_at': datetime.now().isoformat()
            }

            success = self.db_manager.update_session(session_id, update_data)

            if success:
                profit = return_amount - final_investment
                profit_text = f"{profit:+,}円"

                if profit > 0:
                    self.show_validation_success(
                        f"遊技終了！収支: {profit_text} おめでとうございます！")
                elif profit == 0:
                    st.info(f"🤝 遊技終了！収支: {profit_text} 引き分けです。")
                else:
                    self.show_validation_warning(
                        f"遊技終了！収支: {profit_text} 次回頑張りましょう！")

                # Clear active session
                st.session_state.active_session = None
                st.rerun()
            else:
                st.error("セッションの更新に失敗しました。")

        except ValidationError as e:
            st.error(f"入力エラー: {e.message}")
            st.session_state.form_errors[e.field_name] = e.message

        except DatabaseError as e:
            st.error(f"データベースエラー: {e}")
            self.logger.error(f"Database error in session end: {e}")

        except Exception as e:
            st.error("予期しないエラーが発生しました。")
            self.logger.error(f"Unexpected error in session end: {e}")

    def validate_session_start_input(self, session_date: date, start_time: time,
                                     store_name: str, machine_name: str,
                                     initial_investment: int) -> Dict[str, str]:
        """
        Validate session start input data.

        Args:
            session_date: The session date
            start_time: The session start time
            store_name: The store name
            machine_name: The machine name
            initial_investment: The initial investment amount

        Returns:
            Dict[str, str]: Dictionary of field names to error messages
        """
        errors = {}

        # Validate required fields
        if not store_name or not store_name.strip():
            errors['store_name'] = "店舗名は必須です"
        elif len(store_name.strip()) < 2:
            errors['store_name'] = "店舗名は2文字以上で入力してください"
        elif len(store_name.strip()) > 50:
            errors['store_name'] = "店舗名は50文字以下で入力してください"

        if not machine_name or not machine_name.strip():
            errors['machine_name'] = "機種名は必須です"
        elif len(machine_name.strip()) < 2:
            errors['machine_name'] = "機種名は2文字以上で入力してください"
        elif len(machine_name.strip()) > 100:
            errors['machine_name'] = "機種名は100文字以下で入力してください"

        # Validate date
        if session_date > date.today():
            errors['session_date'] = "未来の日付は選択できません"

        # Validate investment amount
        if initial_investment <= 0:
            errors['initial_investment'] = "開始投資額は1円以上で入力してください"
        elif initial_investment > 1000000:
            errors['initial_investment'] = "開始投資額は100万円以下で入力してください"

        # Validate time logic (not too far in the future for today's date)
        if session_date == date.today():
            current_time = datetime.now().time()
            if start_time > current_time:
                errors['start_time'] = "未来の時間は選択できません"

        return errors

    def validate_session_end_input(self, session_data: Dict[str, Any],
                                   end_time: time, final_investment: int,
                                   return_amount: int) -> Dict[str, str]:
        """
        Validate session end input data.

        Args:
            session_data: The current session data
            end_time: The session end time
            final_investment: The final investment amount
            return_amount: The return amount

        Returns:
            Dict[str, str]: Dictionary of field names to error messages
        """
        errors = {}

        # Get start time for comparison
        start_datetime = datetime.fromisoformat(session_data['start_time'])
        session_date = start_datetime.date()
        start_time = start_datetime.time()

        # Validate end time (only check future time if session is today)
        if session_date == date.today():
            current_time = datetime.now().time()
            if end_time > current_time:
                errors['end_time'] = "未来の時間は選択できません"

        if end_time <= start_time:
            errors['end_time'] = "終了時間は開始時間より後である必要があります"

        # Validate final investment
        initial_investment = session_data['initial_investment']
        if final_investment < initial_investment:
            errors['final_investment'] = f"最終投資額は開始投資額（{initial_investment:,}円）以上である必要があります"
        elif final_investment > 1000000:
            errors['final_investment'] = "最終投資額は100万円以下で入力してください"

        # Validate return amount
        if return_amount < 0:
            errors['return_amount'] = "回収金額は0円以上で入力してください"
        elif return_amount > 10000000:
            errors['return_amount'] = "回収金額は1000万円以下で入力してください"

        # Validate logical constraints
        if return_amount > final_investment * 10:
            errors['return_amount'] = "回収金額が投資額に対して異常に高い値です。確認してください"

        return errors

    def display_validation_errors(self, errors: Dict[str, str]) -> None:
        """
        Display validation errors to the user.

        Args:
            errors: Dictionary of field names to error messages
        """
        if errors:
            st.error("⚠️ 入力内容に問題があります:")
            for field, message in errors.items():
                st.error(f"• {message}")

    def validate_required_fields(self, **fields) -> Dict[str, str]:
        """
        Generic validation for required fields.

        Args:
            **fields: Field name to value mapping

        Returns:
            Dict[str, str]: Dictionary of field names to error messages
        """
        errors = {}

        for field_name, value in fields.items():
            if value is None:
                errors[field_name] = f"{field_name}は必須です"
            elif isinstance(value, str) and not value.strip():
                errors[field_name] = f"{field_name}は必須です"
            elif isinstance(value, (int, float)) and value < 0:
                errors[field_name] = f"{field_name}は0以上で入力してください"

        return errors

    def validate_numeric_input(self, value: int, field_name: str,
                               min_value: int = 0, max_value: int = None) -> Optional[str]:
        """
        Validate numeric input with range checking.

        Args:
            value: The numeric value to validate
            field_name: The field name for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value

        Returns:
            Optional[str]: Error message if validation fails, None otherwise
        """
        if not isinstance(value, (int, float)):
            return f"{field_name}は数値で入力してください"

        if value < min_value:
            return f"{field_name}は{min_value:,}以上で入力してください"

        if max_value is not None and value > max_value:
            return f"{field_name}は{max_value:,}以下で入力してください"

        return None

    def show_validation_success(self, message: str) -> None:
        """
        Show a validation success message with animation.

        Args:
            message: The success message to display
        """
        self.show_animated_success(f"✅ {message}")

    def show_validation_warning(self, message: str) -> None:
        """
        Show a validation warning message with animation.

        Args:
            message: The warning message to display
        """
        st.markdown(f"""
        <div class="stWarning" style="animation: fadeIn 0.5s ease, pulse 2s infinite;">
            <p style="margin: 0; font-weight: bold; text-align: center;">⚠️ {message}</p>
        </div>
        """, unsafe_allow_html=True)

    def clear_form_errors(self) -> None:
        """Clear form errors from session state."""
        st.session_state.form_errors = {}

    def has_form_errors(self) -> bool:
        """
        Check if there are any form errors.

        Returns:
            bool: True if there are form errors, False otherwise
        """
        return bool(st.session_state.form_errors)

    def _render_history_filters(self) -> None:
        """Render filtering controls for history page."""
        st.markdown("### 🔍 フィルター")

        # Initialize filter state if not exists
        if 'history_filters' not in st.session_state:
            st.session_state.history_filters = {
                'date_range': None,
                'store_filter': '',
                'machine_filter': '',
                'completed_only': False,
                'profit_filter': 'すべて'
            }

        with st.expander("フィルター設定", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                # Date range filter
                st.markdown("**期間指定**")
                date_filter_type = st.radio(
                    "期間選択",
                    ["すべて", "今月", "先月", "カスタム"],
                    key="date_filter_type",
                    horizontal=True
                )

                date_range = None
                if date_filter_type == "今月":
                    from datetime import date
                    today = date.today()
                    start_date = date(today.year, today.month, 1)
                    if today.month == 12:
                        end_date = date(today.year + 1, 1, 1) - \
                            timedelta(days=1)
                    else:
                        end_date = date(
                            today.year, today.month + 1, 1) - timedelta(days=1)
                    date_range = (datetime.combine(start_date, datetime.min.time()),
                                  datetime.combine(end_date, datetime.max.time()))

                elif date_filter_type == "先月":
                    from datetime import date
                    today = date.today()
                    if today.month == 1:
                        start_date = date(today.year - 1, 12, 1)
                        end_date = date(today.year, 1, 1) - timedelta(days=1)
                    else:
                        start_date = date(today.year, today.month - 1, 1)
                        end_date = date(today.year, today.month,
                                        1) - timedelta(days=1)
                    date_range = (datetime.combine(start_date, datetime.min.time()),
                                  datetime.combine(end_date, datetime.max.time()))

                elif date_filter_type == "カスタム":
                    col_start, col_end = st.columns(2)
                    with col_start:
                        start_date = st.date_input(
                            "開始日", key="custom_start_date")
                    with col_end:
                        end_date = st.date_input("終了日", key="custom_end_date")

                    if start_date and end_date:
                        if start_date <= end_date:
                            date_range = (datetime.combine(start_date, datetime.min.time()),
                                          datetime.combine(end_date, datetime.max.time()))
                        else:
                            st.error("開始日は終了日より前である必要があります")

                st.session_state.history_filters['date_range'] = date_range

            with col2:
                # Store and machine filters
                st.markdown("**店舗・機種フィルター**")
                store_filter = st.text_input(
                    "店舗名で絞り込み",
                    value=st.session_state.history_filters['store_filter'],
                    placeholder="例: マルハン",
                    key="store_filter_input"
                )
                st.session_state.history_filters['store_filter'] = store_filter

                machine_filter = st.text_input(
                    "機種名で絞り込み",
                    value=st.session_state.history_filters['machine_filter'],
                    placeholder="例: シンフォギア",
                    key="machine_filter_input"
                )
                st.session_state.history_filters['machine_filter'] = machine_filter

                # Completed sessions only filter
                completed_only = st.checkbox(
                    "完了したセッションのみ表示",
                    value=st.session_state.history_filters['completed_only'],
                    key="completed_only_filter"
                )
                st.session_state.history_filters['completed_only'] = completed_only

                # Profit/Loss filter
                profit_filter = st.selectbox(
                    "収支フィルター",
                    ["すべて", "勝利のみ", "敗北のみ", "引き分けのみ"],
                    index=["すべて", "勝利のみ", "敗北のみ", "引き分けのみ"].index(
                        st.session_state.history_filters['profit_filter']
                    ),
                    key="profit_filter_select"
                )
                st.session_state.history_filters['profit_filter'] = profit_filter

                # Sorting options
                sort_options = ["日付（新しい順）", "日付（古い順）",
                                "収支（高い順）", "収支（低い順）", "投資額（高い順）", "投資額（低い順）"]
                if 'sort_option' not in st.session_state.history_filters:
                    st.session_state.history_filters['sort_option'] = "日付（新しい順）"

                sort_option = st.selectbox(
                    "並び順",
                    sort_options,
                    index=sort_options.index(
                        st.session_state.history_filters['sort_option']),
                    key="sort_option_select"
                )
                st.session_state.history_filters['sort_option'] = sort_option

            # Clear filters button
            if st.button("🗑️ フィルターをクリア", key="clear_filters"):
                st.session_state.history_filters = {
                    'date_range': None,
                    'store_filter': '',
                    'machine_filter': '',
                    'completed_only': False,
                    'profit_filter': 'すべて',
                    'sort_option': '日付（新しい順）'
                }
                st.rerun()

    def _render_history_list(self) -> None:
        """Render the list of gaming sessions with filtering applied."""
        try:
            user_id = st.session_state.user_id
            filters = st.session_state.history_filters

            # Get sessions from database with date range filter
            sessions = self.db_manager.get_sessions_as_dict(
                user_id=user_id,
                date_range=filters.get('date_range'),
                limit=100  # Limit to prevent performance issues
            )

            # Apply additional filters
            filtered_sessions = self._apply_session_filters(sessions, filters)

            # Apply sorting
            sorted_sessions = self._apply_session_sorting(
                filtered_sessions, filters)

            if not sorted_sessions:
                self._render_no_history_message()
                return

            # Display session count and active filters
            self._render_filter_summary(sorted_sessions, filters)

            # Render sessions
            for session in sorted_sessions:
                self._render_session_card(session)

        except DatabaseError as e:
            st.error(f"履歴の取得に失敗しました: {e}")
        except Exception as e:
            st.error("予期しないエラーが発生しました")
            self.logger.error(f"Error in history list rendering: {e}")

    def _apply_session_filters(self, sessions: List[Dict[str, Any]],
                               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply additional filters to sessions list.

        Args:
            sessions: List of session dictionaries
            filters: Filter criteria

        Returns:
            List of filtered session dictionaries
        """
        filtered = sessions

        # Filter by store name
        if filters.get('store_filter'):
            store_filter = filters['store_filter'].lower()
            filtered = [s for s in filtered
                        if store_filter in s.get('store_name', '').lower()]

        # Filter by machine name
        if filters.get('machine_filter'):
            machine_filter = filters['machine_filter'].lower()
            filtered = [s for s in filtered
                        if machine_filter in s.get('machine_name', '').lower()]

        # Filter by completion status
        if filters.get('completed_only'):
            filtered = [s for s in filtered if s.get('is_completed', False)]

        # Filter by profit/loss
        profit_filter = filters.get('profit_filter', 'すべて')
        if profit_filter != 'すべて':
            if profit_filter == '勝利のみ':
                filtered = [s for s in filtered
                            if s.get('is_completed', False) and s.get('profit', 0) > 0]
            elif profit_filter == '敗北のみ':
                filtered = [s for s in filtered
                            if s.get('is_completed', False) and s.get('profit', 0) < 0]
            elif profit_filter == '引き分けのみ':
                filtered = [s for s in filtered
                            if s.get('is_completed', False) and s.get('profit', 0) == 0]

        return filtered

    def _apply_session_sorting(self, sessions: List[Dict[str, Any]],
                               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply sorting to sessions list.

        Args:
            sessions: List of session dictionaries
            filters: Filter criteria including sort option

        Returns:
            List of sorted session dictionaries
        """
        sort_option = filters.get('sort_option', '日付（新しい順）')

        if sort_option == '日付（新しい順）':
            return sorted(sessions, key=lambda s: s.get('date', ''), reverse=True)
        elif sort_option == '日付（古い順）':
            return sorted(sessions, key=lambda s: s.get('date', ''))
        elif sort_option == '収支（高い順）':
            # Only sort completed sessions by profit, put incomplete at end
            completed = [s for s in sessions if s.get('is_completed', False)]
            incomplete = [s for s in sessions if not s.get(
                'is_completed', False)]
            completed_sorted = sorted(
                completed, key=lambda s: s.get('profit', 0), reverse=True)
            return completed_sorted + incomplete
        elif sort_option == '収支（低い順）':
            # Only sort completed sessions by profit, put incomplete at end
            completed = [s for s in sessions if s.get('is_completed', False)]
            incomplete = [s for s in sessions if not s.get(
                'is_completed', False)]
            completed_sorted = sorted(
                completed, key=lambda s: s.get('profit', 0))
            return completed_sorted + incomplete
        elif sort_option == '投資額（高い順）':
            return sorted(sessions, key=lambda s: s.get('final_investment') or s.get('initial_investment', 0), reverse=True)
        elif sort_option == '投資額（低い順）':
            return sorted(sessions, key=lambda s: s.get('final_investment') or s.get('initial_investment', 0))
        else:
            # Default to date descending
            return sorted(sessions, key=lambda s: s.get('date', ''), reverse=True)

    def _render_session_card(self, session: Dict[str, Any]) -> None:
        """
        Render a single session as a card with details.

        Args:
            session: Session dictionary
        """
        # Parse dates for display
        session_date = datetime.fromisoformat(
            session['date']).strftime('%Y/%m/%d')
        start_time = datetime.fromisoformat(
            session['start_time']).strftime('%H:%M')

        # Determine session status and colors
        is_completed = session.get('is_completed', False)
        profit = session.get('profit', 0) if is_completed else None

        if is_completed:
            if profit > 0:
                status_icon = "💰"
                status_text = "勝利"
            elif profit == 0:
                status_icon = "🤝"
                status_text = "引き分け"
            else:
                status_icon = "📉"
                status_text = "敗北"
        else:
            status_icon = "⏳"
            status_text = "進行中"

        # Get session status class for background
        session_class = self.get_session_status_class(
            profit) if is_completed else "session-neutral"

        # Create expandable card
        with st.expander(
            f"{status_icon} {session_date} {session['store_name']} - {session['machine_name']} ({status_text})",
            expanded=False
        ):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"""
                <div class="session-card {session_class}">
                    <h4>基本情報</h4>
                    <p><strong>日付:</strong> {session_date}</p>
                    <p><strong>開始時間:</strong> {start_time}</p>
                    <p><strong>店舗:</strong> {session['store_name']}</p>
                    <p><strong>機種:</strong> {session['machine_name']}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if is_completed:
                    end_time = datetime.fromisoformat(
                        session['end_time']).strftime('%H:%M')
                    profit_class = self.get_profit_color_class(profit)
                    investment_class = self.get_investment_level_class(
                        session.get('final_investment', 0))

                    st.markdown(f"""
                    <div class="session-card {session_class}">
                        <h4>収支情報</h4>
                        <p><strong>終了時間:</strong> {end_time}</p>
                        <p><strong>投資額:</strong> <span class="{investment_class}">{session.get('final_investment', 0):,}円</span></p>
                        <p><strong>回収額:</strong> {session.get('return_amount', 0):,}円</p>
                        <p><strong>収支:</strong> <span class="{profit_class}">{profit:+,}円</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    investment_class = self.get_investment_level_class(
                        session['initial_investment'])
                    st.markdown(f"""
                    <div class="session-card {session_class}">
                        <h4>進行中</h4>
                        <p><strong>開始投資額:</strong> <span class="{investment_class}">{session['initial_investment']:,}円</span></p>
                        <p><strong>状態:</strong> <span style="color: #8A2BE2; font-weight: bold;">遊技中</span></p>
                        <p>終了時に結果を入力してください</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Action buttons for session management
            if is_completed:
                col_edit, col_delete = st.columns(2)
                with col_edit:
                    if st.button(f"✏️ 編集", key=f"edit_{session['id']}", use_container_width=True):
                        st.info("編集機能は今後実装予定です")
                with col_delete:
                    if st.button(f"🗑️ 削除", key=f"delete_{session['id']}", use_container_width=True):
                        st.info("削除機能は今後実装予定です")
            else:
                if st.button(f"✅ 遊技終了", key=f"complete_{session['id']}", use_container_width=True):
                    # Set this session as active and switch to record page
                    st.session_state.active_session = session
                    st.session_state.current_page = 'record'
                    st.rerun()

    def _render_no_history_message(self) -> None:
        """Render message when no history data is available."""
        filters = st.session_state.history_filters

        # Check if any filters are applied
        has_filters = (
            filters.get('date_range') is not None or
            filters.get('store_filter') or
            filters.get('machine_filter') or
            filters.get('completed_only') or
            filters.get('profit_filter', 'すべて') != 'すべて'
        )

        if has_filters:
            # Show filtered no results message
            st.markdown("""
            <div class="stat-card" style="text-align: center; padding: 40px;">
                <h3>🔍 フィルター条件に一致する記録がありません</h3>
                <p>検索条件を変更して再度お試しください。</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ フィルターをクリア", key="no_results_clear_filters", use_container_width=True):
                    st.session_state.history_filters = {
                        'date_range': None,
                        'store_filter': '',
                        'machine_filter': '',
                        'completed_only': False,
                        'profit_filter': 'すべて',
                        'sort_option': '日付（新しい順）'
                    }
                    st.rerun()
            with col2:
                if st.button("🎮 新しい遊技を開始", key="no_results_start", use_container_width=True):
                    st.session_state.current_page = 'record'
                    st.rerun()
        else:
            # Show no data at all message
            st.markdown("""
            <div class="stat-card" style="text-align: center; padding: 40px;">
                <h3>📭 履歴データがありません</h3>
                <p>まだ遊技記録がありません。</p>
                <p>「遊技記録」ページから新しいセッションを開始してみましょう！</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🎮 新しい遊技を開始", key="no_history_start", use_container_width=True):
                st.session_state.current_page = 'record'
                st.rerun()

    def _render_filter_summary(self, filtered_sessions: List[Dict[str, Any]],
                               filters: Dict[str, Any]) -> None:
        """
        Render a summary of applied filters and results count.

        Args:
            filtered_sessions: List of filtered session dictionaries
            filters: Applied filter criteria
        """
        # Display session count
        st.markdown(f"**{len(filtered_sessions)}件の記録が見つかりました**")

        # Show active filters
        active_filters = []

        if filters.get('date_range'):
            start_date, end_date = filters['date_range']
            active_filters.append(
                f"📅 期間: {start_date.strftime('%Y/%m/%d')} - {end_date.strftime('%Y/%m/%d')}")

        if filters.get('store_filter'):
            active_filters.append(f"🏪 店舗: {filters['store_filter']}")

        if filters.get('machine_filter'):
            active_filters.append(f"🎰 機種: {filters['machine_filter']}")

        if filters.get('completed_only'):
            active_filters.append("✅ 完了セッションのみ")

        if filters.get('profit_filter', 'すべて') != 'すべて':
            active_filters.append(f"💰 収支: {filters['profit_filter']}")

        if active_filters:
            st.markdown("**適用中のフィルター:**")
            for filter_desc in active_filters:
                st.markdown(f"• {filter_desc}")
            st.markdown("---")

    def _render_export_page(self) -> None:
        """Render the data export page."""
        st.markdown("## 📤 データエクスポート")

        try:
            user_id = st.session_state.user_id

            # Get all sessions for the user
            all_sessions = self.db_manager.get_sessions(user_id)

            if not all_sessions:
                st.info("📭 エクスポートできるデータがありません。まず遊技記録を追加してください。")
                if st.button("🎮 新しい遊技を開始", key="export_start_new", use_container_width=True):
                    st.session_state.current_page = 'record'
                    st.rerun()
                return

            # Export options section
            st.markdown("### 🔧 エクスポート設定")

            col1, col2 = st.columns(2)

            with col1:
                # Date range selection
                st.markdown("**📅 期間選択**")
                date_option = st.radio(
                    "期間",
                    ["すべて", "期間指定"],
                    key="export_date_option",
                    horizontal=True
                )

                date_range = None
                if date_option == "期間指定":
                    col_start, col_end = st.columns(2)
                    with col_start:
                        start_date = st.date_input(
                            "開始日",
                            value=datetime.now().date() - timedelta(days=30),
                            key="export_start_date"
                        )
                    with col_end:
                        end_date = st.date_input(
                            "終了日",
                            value=datetime.now().date(),
                            key="export_end_date"
                        )

                    if start_date <= end_date:
                        date_range = (
                            datetime.combine(start_date, datetime.min.time()),
                            datetime.combine(end_date, datetime.max.time())
                        )
                    else:
                        st.error("開始日は終了日より前である必要があります")
                        return

            with col2:
                # Export options
                st.markdown("**⚙️ オプション**")
                include_incomplete = st.checkbox(
                    "未完了セッションを含める",
                    value=False,
                    key="export_include_incomplete"
                )

                include_stats = st.checkbox(
                    "統計情報を含める (PDF)",
                    value=True,
                    key="export_include_stats"
                )

            # Filter sessions based on date range
            if date_range:
                filtered_sessions = [
                    s for s in all_sessions
                    if date_range[0] <= s.date <= date_range[1]
                ]
            else:
                filtered_sessions = all_sessions

            # Show export preview
            self._render_export_preview(filtered_sessions, include_incomplete)

            # Export buttons
            st.markdown("### 📥 エクスポート実行")

            if filtered_sessions:
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("📊 CSV形式でエクスポート", key="export_csv", use_container_width=True):
                        self._handle_csv_export(
                            filtered_sessions, include_incomplete, date_range)

                with col2:
                    if st.button("📄 PDF形式でエクスポート", key="export_pdf", use_container_width=True):
                        self._handle_pdf_export(
                            filtered_sessions, user_id, include_stats, date_range)
            else:
                st.warning("選択した条件に一致するデータがありません。")

        except DatabaseError as e:
            st.error(f"データベースエラー: {e}")
            self.logger.error(f"Database error in export page: {e}")
        except Exception as e:
            st.error("エクスポートページの表示中にエラーが発生しました。")
            self.logger.error(f"Unexpected error in export page: {e}")

    def _render_export_preview(self, sessions: List[GameSession], include_incomplete: bool) -> None:
        """Render export preview section."""
        st.markdown("### 📋 エクスポートプレビュー")

        # Get export summary
        export_summary = self.export_manager.get_export_summary(sessions)

        # Display summary cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h4>総セッション数</h4>
                <p style="font-size: 2em; color: #8A2BE2;">{export_summary['total_sessions']}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h4>完了セッション</h4>
                <p style="font-size: 2em; color: #00BFFF;">{export_summary['completed_sessions']}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            profit_class = self.get_profit_color_class(
                export_summary['total_profit'])
            st.markdown(f"""
            <div class="stat-card">
                <h4>総収支</h4>
                <p class="{profit_class}" style="font-size: 1.5em; font-weight: bold;">
                    {export_summary['total_profit']:+,}円
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            date_range_text = "全期間"
            if export_summary.get('date_range'):
                dr = export_summary['date_range']
                date_range_text = f"{dr['start']} ～ {dr['end']}"

            st.markdown(f"""
            <div class="stat-card">
                <h4>対象期間</h4>
                <p style="font-size: 1em; color: #FFD700;">{date_range_text}</p>
            </div>
            """, unsafe_allow_html=True)

        # Show validation results
        validation_result = self.export_manager.validate_export_data(sessions)

        if validation_result['warnings']:
            with st.expander("⚠️ 注意事項", expanded=False):
                for warning in validation_result['warnings']:
                    st.warning(warning)

        if validation_result['errors']:
            st.error("エクスポートできません:")
            for error in validation_result['errors']:
                st.error(f"• {error}")

        # Show estimated file sizes
        col1, col2 = st.columns(2)
        with col1:
            st.info(
                f"📊 CSV推定サイズ: {export_summary.get('csv_size_estimate', 'Unknown')}")
        with col2:
            st.info(
                f"📄 PDF推定サイズ: {export_summary.get('pdf_size_estimate', 'Unknown')}")

    def _handle_csv_export(self, sessions: List[GameSession], include_incomplete: bool,
                           date_range: Optional[tuple] = None) -> None:
        """Handle CSV export process."""
        try:
            with st.spinner("CSVファイルを生成中..."):
                # Generate CSV data
                csv_data = self.export_manager.export_to_csv(
                    sessions, include_incomplete)

                # Generate filename
                filename = self.export_manager.generate_export_filename(
                    'csv', st.session_state.user_id, date_range
                )

                # Provide download button
                st.download_button(
                    label="📥 CSVファイルをダウンロード",
                    data=csv_data,
                    file_name=filename,
                    mime="text/csv",
                    key="download_csv"
                )

                st.success(f"✅ CSVファイルが正常に生成されました！ ({len(sessions)}件のセッション)")

        except ExportError as e:
            st.error(f"CSVエクスポートエラー: {e}")
            self.logger.error(f"CSV export error: {e}")
        except Exception as e:
            st.error("CSVエクスポート中に予期しないエラーが発生しました。")
            self.logger.error(f"Unexpected CSV export error: {e}")

    def _handle_pdf_export(self, sessions: List[GameSession], user_id: str,
                           include_stats: bool, date_range: Optional[tuple] = None) -> None:
        """Handle PDF export process."""
        try:
            with st.spinner("PDFレポートを生成中..."):
                # Generate PDF data
                pdf_data = self.export_manager.export_to_pdf(
                    sessions, user_id, include_stats
                )

                # Generate filename
                filename = self.export_manager.generate_export_filename(
                    'pdf', user_id, date_range
                )

                # Provide download button
                st.download_button(
                    label="📥 PDFレポートをダウンロード",
                    data=pdf_data,
                    file_name=filename,
                    mime="application/pdf",
                    key="download_pdf"
                )

                st.success(f"✅ PDFレポートが正常に生成されました！ ({len(sessions)}件のセッション)")

        except ExportError as e:
            st.error(f"PDFエクスポートエラー: {e}")
            self.logger.error(f"PDF export error: {e}")
        except Exception as e:
            st.error("PDFエクスポート中に予期しないエラーが発生しました。")
            self.logger.error(f"Unexpected PDF export error: {e}")

    def render_export_options(self) -> None:
        """Render export options in other pages (like history)."""
        if st.button("📤 データをエクスポート", key="quick_export", use_container_width=True):
            st.session_state.current_page = 'export'
            st.rerun()
