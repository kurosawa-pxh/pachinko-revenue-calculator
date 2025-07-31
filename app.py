"""
メインアプリケーションエントリーポイント - Pachinko Revenue Calculator

Streamlit アプリケーションのメインエントリーポイント。
セッション状態管理、ページルーティング、ナビゲーションを実装。
"""

from src.error_handler import handle_error, ErrorCategory, ErrorSeverity
from src.pachinko_app import PachinkoApp
import streamlit as st
import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


# Page configuration
st.set_page_config(
    page_title="勝てるクン - パチンコ収支管理",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "勝てるクン - パチンコ収支管理アプリ"
    }
)


class StreamlitApp:
    """
    Streamlit アプリケーションのメインクラス。

    セッション状態管理、ページルーティング、ナビゲーションを担当。
    """

    def __init__(self):
        """Initialize the Streamlit application."""
        self.logger = logging.getLogger('streamlit_app')
        self.app: Optional[PachinkoApp] = None

        # Initialize session state
        self._initialize_session_state()

        # Initialize the main application
        self._initialize_app()

    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        # Authentication state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False

        if 'username' not in st.session_state:
            st.session_state.username = None

        if 'user_id' not in st.session_state:
            st.session_state.user_id = None

        # Navigation state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'login'

        if 'previous_page' not in st.session_state:
            st.session_state.previous_page = None

        # Application state
        if 'app_initialized' not in st.session_state:
            st.session_state.app_initialized = False

        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None

        if 'session_in_progress' not in st.session_state:
            st.session_state.session_in_progress = False

        # UI state
        if 'show_sidebar' not in st.session_state:
            st.session_state.show_sidebar = True

        if 'theme_mode' not in st.session_state:
            st.session_state.theme_mode = 'flashy'

        # Error handling state
        if 'last_error' not in st.session_state:
            st.session_state.last_error = None

        if 'error_count' not in st.session_state:
            st.session_state.error_count = 0

    def _initialize_app(self) -> None:
        """Initialize the main PachinkoApp instance."""
        try:
            if not st.session_state.app_initialized:
                # Create configuration based on environment
                config = self._get_app_config()

                # Initialize the main application
                self.app = PachinkoApp(config)

                if self.app.is_ready():
                    st.session_state.app_initialized = True
                    self.logger.info("Streamlit app initialized successfully")
                else:
                    raise RuntimeError(
                        "Failed to initialize application components")
            else:
                # Reuse existing app instance
                if hasattr(st.session_state, '_pachinko_app'):
                    self.app = st.session_state._pachinko_app
                else:
                    # Recreate if lost
                    config = self._get_app_config()
                    self.app = PachinkoApp(config)

            # Store app instance in session state
            st.session_state._pachinko_app = self.app

        except Exception as e:
            self.logger.error(f"Failed to initialize app: {e}")
            st.error("アプリケーションの初期化に失敗しました。ページを再読み込みしてください。")
            try:
                handle_error(e, ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL)
            except Exception as handler_error:
                self.logger.error(f"Error handler failed: {handler_error}")
                st.error(f"エラー処理中に問題が発生しました: {str(e)}")

    def _get_app_config(self) -> Dict[str, Any]:
        """Get application configuration for Streamlit deployment."""
        return {
            'database': {
                'path': os.getenv('DATABASE_PATH', 'pachinko_data.db'),
                'auth_path': os.getenv('AUTH_DATABASE_PATH', 'pachinko_auth.db'),
                'enable_encryption': os.getenv('ENABLE_ENCRYPTION', 'true').lower() == 'true'
            },
            'ui': {
                'theme': 'flashy',
                'enable_animations': True,
                'mobile_optimized': True
            },
            'features': {
                'offline_mode': True,
                'export_enabled': True,
                'advanced_stats': True
            },
            'security': {
                'session_timeout': 3600,
                'max_login_attempts': 5,
                'password_min_length': 8
            },
            'deployment': {
                'environment': os.getenv('ENVIRONMENT', 'production'),
                'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true'
            }
        }

    def run(self) -> None:
        """Run the main Streamlit application."""
        try:
            # Check if app is properly initialized
            if not self.app or not self.app.is_ready():
                st.error("アプリケーションが正しく初期化されていません。")
                st.stop()

            # Check free tier limits before proceeding
            if not self.app.check_free_tier_limits():
                st.stop()

            # Handle authentication
            if not st.session_state.authenticated:
                self._render_authentication_page()
            else:
                # Render main application
                self._render_main_application()

        except Exception as e:
            self.logger.error(f"Error in main application loop: {e}")
            st.error("アプリケーションエラーが発生しました。")
            handle_error(e, ErrorCategory.UI, ErrorSeverity.HIGH)

    def _render_authentication_page(self) -> None:
        """Render the authentication page."""
        try:
            auth_manager = self.app.get_auth_manager()

            # Create authentication UI
            st.title("🎰 勝てるクン - ログイン")
            st.markdown("---")

            # Login/Register tabs
            tab1, tab2 = st.tabs(["ログイン", "新規登録"])

            with tab1:
                self._render_login_form(auth_manager)

            with tab2:
                self._render_register_form(auth_manager)

        except Exception as e:
            self.logger.error(f"Error in authentication page: {e}")
            st.error("認証ページでエラーが発生しました。")

    def _render_login_form(self, auth_manager) -> None:
        """Render the login form."""
        with st.form("login_form"):
            st.subheader("ログイン")

            username = st.text_input("ユーザー名")
            password = st.text_input("パスワード", type="password")

            if st.form_submit_button("ログイン"):
                if username and password:
                    try:
                        success, user_info = auth_manager.login_user(
                            username, password)
                        if success and user_info:
                            st.session_state.authenticated = True
                            st.session_state.username = user_info['username']
                            st.session_state.user_id = user_info['id']
                            st.session_state.current_page = 'dashboard'
                            st.rerun()
                        else:
                            st.error("ユーザー名またはパスワードが正しくありません。")
                    except Exception as e:
                        st.error("ログインに失敗しました。")
                        self.logger.error(f"Login error: {e}")
                else:
                    st.error("ユーザー名とパスワードを入力してください。")

    def _render_register_form(self, auth_manager) -> None:
        """Render the registration form."""
        with st.form("register_form"):
            st.subheader("新規登録")

            username = st.text_input("ユーザー名（新規）")
            email = st.text_input("メールアドレス", placeholder="example@email.com")
            password = st.text_input("パスワード（新規）", type="password")
            password_confirm = st.text_input("パスワード確認", type="password")

            if st.form_submit_button("登録"):
                if username and email and password and password_confirm:
                    if password != password_confirm:
                        st.error("パスワードが一致しません。")
                    else:
                        try:
                            if auth_manager.register_user(username, email, password):
                                st.success("アカウントが作成されました。ログインしてください。")
                            else:
                                st.error("アカウントの作成に失敗しました。")
                        except Exception as e:
                            st.error("登録に失敗しました。")
                            self.logger.error(f"Registration error: {e}")
                else:
                    st.error("すべてのフィールドを入力してください。")

    def _render_main_application(self) -> None:
        """Render the main application interface."""
        try:
            # Get UI manager
            ui_manager = self.app.get_ui_manager()

            # Render navigation sidebar
            self._render_navigation_sidebar()

            # Render main content based on current page
            if st.session_state.current_page == 'dashboard':
                self._render_dashboard_page(ui_manager)
            elif st.session_state.current_page == 'input':
                self._render_input_page(ui_manager)
            elif st.session_state.current_page == 'history':
                self._render_history_page(ui_manager)
            elif st.session_state.current_page == 'stats':
                self._render_stats_page(ui_manager)
            elif st.session_state.current_page == 'export':
                self._render_export_page(ui_manager)
            elif st.session_state.current_page == 'admin':
                self._render_admin_page(ui_manager)
            else:
                st.error("不明なページです。")

        except Exception as e:
            self.logger.error(f"Error in main application: {e}")
            st.error("メインアプリケーションでエラーが発生しました。")

    def _render_navigation_sidebar(self) -> None:
        """Render the navigation sidebar."""
        with st.sidebar:
            st.title("🎰 勝てるクン")
            st.markdown(f"ようこそ、{st.session_state.username}さん！")
            st.markdown("---")

            # Navigation buttons
            if st.button("📊 ダッシュボード", use_container_width=True):
                st.session_state.current_page = 'dashboard'
                st.rerun()

            if st.button("📝 遊技記録", use_container_width=True):
                st.session_state.current_page = 'input'
                st.rerun()

            if st.button("📋 履歴", use_container_width=True):
                st.session_state.current_page = 'history'
                st.rerun()

            if st.button("📈 統計", use_container_width=True):
                st.session_state.current_page = 'stats'
                st.rerun()

            if st.button("💾 エクスポート", use_container_width=True):
                st.session_state.current_page = 'export'
                st.rerun()

            # Admin/deployment page (only show in production or for admin users)
            if os.getenv('ENVIRONMENT') == 'production' or os.getenv('DEBUG', 'false').lower() == 'true':
                if st.button("⚙️ システム状況", use_container_width=True):
                    st.session_state.current_page = 'admin'
                    st.rerun()

            st.markdown("---")

            # Logout button
            if st.button("🚪 ログアウト", use_container_width=True):
                self._logout()

    def _render_dashboard_page(self, ui_manager) -> None:
        """Render the dashboard page."""
        st.title("📊 ダッシュボード")

        try:
            # Get database manager
            db_manager = self.app.get_database_manager()
            stats_calculator = self.app.get_stats_calculator()

            # Simple dashboard implementation
            st.subheader("収支サマリー")

            # Get user sessions
            user_id = st.session_state.user_id
            sessions = db_manager.get_sessions(user_id, limit=10)

            if sessions:
                # Calculate basic stats
                total_profit = sum(session.profit or 0 for session in sessions)
                total_sessions = len(sessions)
                win_sessions = len(
                    [s for s in sessions if (s.profit or 0) > 0])
                win_rate = (win_sessions / total_sessions *
                            100) if total_sessions > 0 else 0

                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("総収支", f"¥{total_profit:,}")
                with col2:
                    st.metric("総セッション数", total_sessions)
                with col3:
                    st.metric("勝率", f"{win_rate:.1f}%")

                # Recent sessions
                st.subheader("最近のセッション")
                for session in sessions[:5]:
                    with st.container():
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.write(f"📅 {session.date}")
                        with col2:
                            st.write(f"🏪 {session.store_name}")
                        with col3:
                            st.write(f"🎰 {session.machine_name}")
                        with col4:
                            profit_color = "green" if (
                                session.profit or 0) >= 0 else "red"
                            st.markdown(f"<span style='color: {profit_color}'>¥{session.profit or 0:,}</span>",
                                        unsafe_allow_html=True)
            else:
                st.info("まだセッションが記録されていません。「📝 遊技記録」から記録を開始してください。")

        except Exception as e:
            st.error("ダッシュボードの表示中にエラーが発生しました。")
            self.logger.error(f"Dashboard error: {e}")

    def _render_input_page(self, ui_manager) -> None:
        """Render the input page."""
        st.title("📝 遊技記録")

        try:
            db_manager = self.app.get_database_manager()
            user_id = st.session_state.user_id

            # Simple input form
            with st.form("session_input"):
                st.subheader("新しいセッションを記録")

                col1, col2 = st.columns(2)
                with col1:
                    date = st.date_input("日付", value=datetime.now().date())
                    store_name = st.text_input(
                        "店舗名", placeholder="例: パチンコ店ABC")
                    machine_name = st.text_input(
                        "機種名", placeholder="例: CR花の慶次")

                with col2:
                    start_time = st.time_input(
                        "開始時間", value=datetime.now().time())
                    end_time = st.time_input(
                        "終了時間", value=datetime.now().time())
                    initial_investment = st.number_input(
                        "投資金額", min_value=0, value=1000, step=100)

                final_investment = st.number_input(
                    "最終投資額", min_value=0, value=initial_investment, step=100)
                return_amount = st.number_input(
                    "回収金額", min_value=0, value=0, step=100)

                if st.form_submit_button("記録する", use_container_width=True):
                    if store_name and machine_name:
                        try:
                            # Create session object
                            from src.models import GameSession

                            profit = return_amount - final_investment

                            session = GameSession(
                                user_id=user_id,
                                date=date,
                                start_time=datetime.combine(date, start_time),
                                end_time=datetime.combine(date, end_time),
                                store_name=store_name,
                                machine_name=machine_name,
                                initial_investment=initial_investment,
                                final_investment=final_investment,
                                return_amount=return_amount,
                                profit=profit,
                                is_completed=True
                            )

                            # Save to database
                            session_id = db_manager.create_session(session)
                            st.success(f"セッションが記録されました！ (ID: {session_id})")

                        except Exception as e:
                            st.error("セッションの記録に失敗しました。")
                            self.logger.error(f"Session creation error: {e}")
                    else:
                        st.error("店舗名と機種名は必須です。")

        except Exception as e:
            st.error("入力ページの表示中にエラーが発生しました。")
            self.logger.error(f"Input page error: {e}")

    def _render_history_page(self, ui_manager) -> None:
        """Render the history page."""
        st.title("📋 遊技履歴")

        try:
            db_manager = self.app.get_database_manager()
            user_id = st.session_state.user_id

            # Get all sessions
            sessions = db_manager.get_sessions(user_id, limit=50)

            if sessions:
                st.subheader(f"履歴 ({len(sessions)}件)")

                # Display sessions in a table-like format
                for i, session in enumerate(sessions):
                    with st.container():
                        col1, col2, col3, col4, col5, col6 = st.columns(6)

                        with col1:
                            st.write(f"📅 {session.date}")
                        with col2:
                            st.write(f"🏪 {session.store_name}")
                        with col3:
                            st.write(f"🎰 {session.machine_name}")
                        with col4:
                            st.write(f"💰 ¥{session.final_investment:,}")
                        with col5:
                            st.write(f"💸 ¥{session.return_amount:,}")
                        with col6:
                            profit = session.profit or 0
                            profit_color = "green" if profit >= 0 else "red"
                            st.markdown(f"<span style='color: {profit_color}'>¥{profit:,}</span>",
                                        unsafe_allow_html=True)

                        if i < len(sessions) - 1:
                            st.divider()
            else:
                st.info("まだ履歴がありません。")

        except Exception as e:
            st.error("履歴の表示中にエラーが発生しました。")
            self.logger.error(f"History page error: {e}")

    def _render_stats_page(self, ui_manager) -> None:
        """Render the statistics page."""
        st.title("📈 統計分析")

        try:
            db_manager = self.app.get_database_manager()
            stats_calculator = self.app.get_stats_calculator()
            user_id = st.session_state.user_id

            # Get sessions for stats
            sessions = db_manager.get_sessions(user_id, limit=100)

            if sessions:
                # Basic statistics
                total_sessions = len(sessions)
                total_investment = sum(
                    session.final_investment for session in sessions)
                total_return = sum(
                    session.return_amount for session in sessions)
                total_profit = total_return - total_investment
                win_sessions = len(
                    [s for s in sessions if (s.profit or 0) > 0])
                win_rate = (win_sessions / total_sessions *
                            100) if total_sessions > 0 else 0

                # Display stats
                st.subheader("基本統計")

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("総セッション数", total_sessions)
                with col2:
                    st.metric("総投資額", f"¥{total_investment:,}")
                with col3:
                    st.metric("総回収額", f"¥{total_return:,}")
                with col4:
                    profit_delta = f"¥{total_profit:,}"
                    st.metric("総収支", profit_delta, delta=profit_delta)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("勝率", f"{win_rate:.1f}%")
                with col2:
                    avg_profit = total_profit / total_sessions if total_sessions > 0 else 0
                    st.metric("平均収支", f"¥{avg_profit:,.0f}")

                # Store analysis
                st.subheader("店舗別分析")
                store_stats = {}
                for session in sessions:
                    store = session.store_name
                    if store not in store_stats:
                        store_stats[store] = {'sessions': 0, 'profit': 0}
                    store_stats[store]['sessions'] += 1
                    store_stats[store]['profit'] += session.profit or 0

                for store, stats in store_stats.items():
                    avg_profit = stats['profit'] / stats['sessions']
                    profit_color = "green" if stats['profit'] >= 0 else "red"
                    st.write(f"🏪 **{store}**: {stats['sessions']}回, "
                             f"<span style='color: {profit_color}'>¥{stats['profit']:,}</span> "
                             f"(平均: ¥{avg_profit:,.0f})", unsafe_allow_html=True)

            else:
                st.info("統計を表示するにはセッションデータが必要です。")

        except Exception as e:
            st.error("統計の表示中にエラーが発生しました。")
            self.logger.error(f"Stats page error: {e}")

    def _render_export_page(self, ui_manager) -> None:
        """Render the export page."""
        st.title("💾 データエクスポート")
        ui_manager.render_export_options()

    def _render_admin_page(self, ui_manager) -> None:
        """Render the admin/system status page."""
        st.title("⚙️ システム状況")

        try:
            deployment_manager = self.app.get_deployment_manager()

            # Display deployment information
            st.subheader("🚀 デプロイメント情報")
            deployment_info = deployment_manager.get_deployment_info()

            col1, col2 = st.columns(2)

            with col1:
                st.metric("環境", deployment_info['environment'])
                st.metric("プラットフォーム", deployment_info['platform'])
                st.metric("Python バージョン",
                          deployment_info['python_version'].split()[0])

            with col2:
                st.metric("Streamlit バージョン",
                          deployment_info['streamlit_version'])
                st.metric("データベース", deployment_info['database_type'])
                st.metric("デプロイ時刻", deployment_info['deployment_time'][:19])

            st.markdown("---")

            # Display resource usage dashboard
            deployment_manager.display_usage_dashboard()

            st.markdown("---")

            # Display health status
            st.subheader("🏥 システムヘルス")
            health_status = self.app.get_health_status()

            if health_status.get('deployment', {}).get('status') == 'healthy':
                st.success("✅ システム正常稼働中")
            elif health_status.get('deployment', {}).get('status') == 'degraded':
                st.warning("⚠️ システムに軽微な問題があります")
            else:
                st.error("❌ システムに問題があります")

            # Show detailed health information
            with st.expander("詳細ヘルス情報"):
                st.json(health_status)

            st.markdown("---")

            # Feature status
            st.subheader("🔧 機能状況")
            features = deployment_info['features_enabled']

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                status = "✅" if features['offline_mode'] else "❌"
                st.write(f"{status} オフラインモード")

            with col2:
                status = "✅" if features['export_enabled'] else "❌"
                st.write(f"{status} エクスポート機能")

            with col3:
                status = "✅" if features['advanced_stats'] else "❌"
                st.write(f"{status} 高度統計")

            with col4:
                status = "✅" if features['animations'] else "❌"
                st.write(f"{status} アニメーション")

            # Manual health check button
            if st.button("🔄 ヘルスチェック実行"):
                with st.spinner("ヘルスチェック実行中..."):
                    health = deployment_manager.check_deployment_health()
                    if health['status'] == 'healthy':
                        st.success("ヘルスチェック完了: システム正常")
                    else:
                        st.error(f"ヘルスチェック完了: {health['status']}")
                        if 'failed_checks' in health:
                            st.error(f"失敗したチェック: {health['failed_checks']}")

        except Exception as e:
            st.error(f"システム状況の取得に失敗しました: {e}")
            self.logger.error(f"Error in admin page: {e}")

    def _logout(self) -> None:
        """Handle user logout."""
        # Clear authentication state
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.session_state.current_page = 'login'

        # Clear session data
        st.session_state.current_session_id = None
        st.session_state.session_in_progress = False

        st.rerun()


def main():
    """Main entry point for the Streamlit application."""
    try:
        # Create and run the Streamlit app
        app = StreamlitApp()
        app.run()

    except Exception as e:
        logging.error(f"Critical error in main: {e}")
        st.error("アプリケーションの起動に失敗しました。")
        st.exception(e)


if __name__ == "__main__":
    main()
