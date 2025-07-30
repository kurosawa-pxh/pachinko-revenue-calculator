"""
Demo script to showcase export functionality.
"""

import streamlit as st
from datetime import datetime, timedelta
import tempfile
import os

from src.models import GameSession
from src.database import DatabaseManager
from src.stats import StatsCalculator
from src.ui_manager import UIManager


def create_demo_data(db_manager: DatabaseManager):
    """Create demo data for export demonstration."""
    demo_sessions = []
    base_date = datetime.now() - timedelta(days=30)

    stores = ["パチンコ太郎", "スロット花子", "大当たり次郎"]
    machines = ["CR戦国乙女", "パチスロ北斗の拳", "CRフィーバー", "沖ドキ"]

    for i in range(15):
        session_date = base_date + timedelta(days=i * 2)

        session = GameSession(
            user_id="demo_user",
            date=session_date,
            start_time=session_date.replace(hour=10 + (i % 4), minute=0),
            store_name=stores[i % len(stores)],
            machine_name=machines[i % len(machines)],
            initial_investment=1000 + (i * 100)
        )

        # Complete most sessions (leave some incomplete for demo)
        if i < 12:
            end_time = session_date.replace(hour=14 + (i % 3), minute=30)
            final_investment = session.initial_investment + (i * 50)
            # Create realistic profit/loss pattern
            if i % 3 == 0:  # Win
                return_amount = final_investment + (i * 300)
            elif i % 3 == 1:  # Small loss
                return_amount = final_investment - (i * 100)
            else:  # Big loss
                return_amount = final_investment - (i * 200)

            session.complete_session(end_time, final_investment, return_amount)

        demo_sessions.append(session)
        db_manager.create_session(session)

    return demo_sessions


def main():
    """Main demo application."""
    st.set_page_config(
        page_title="勝てるクン - エクスポート機能デモ",
        page_icon="🎰",
        layout="wide"
    )

    st.title("🎰 勝てるクン - エクスポート機能デモ")
    st.markdown("---")

    # Initialize components
    if 'db_manager' not in st.session_state:
        # Create temporary database for demo
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        st.session_state.temp_db_path = temp_db.name
        st.session_state.db_manager = DatabaseManager(temp_db.name)
        st.session_state.stats_calculator = StatsCalculator(
            st.session_state.db_manager)
        st.session_state.ui_manager = UIManager(
            st.session_state.db_manager,
            st.session_state.stats_calculator
        )

        # Create demo data
        create_demo_data(st.session_state.db_manager)
        st.success("✅ デモデータを作成しました！")

    # Demo navigation
    demo_option = st.selectbox(
        "デモ機能を選択してください:",
        ["エクスポート機能", "履歴表示", "統計表示"]
    )

    if demo_option == "エクスポート機能":
        st.markdown("## 📤 エクスポート機能デモ")
        st.session_state.current_page = 'export'
        st.session_state.user_id = 'demo_user'
        st.session_state.ui_manager._render_export_page()

    elif demo_option == "履歴表示":
        st.markdown("## 📋 履歴表示デモ")
        st.session_state.current_page = 'history'
        st.session_state.user_id = 'demo_user'
        st.session_state.ui_manager._render_history_page()

    elif demo_option == "統計表示":
        st.markdown("## 📊 統計表示デモ")
        st.session_state.current_page = 'stats'
        st.session_state.user_id = 'demo_user'
        st.session_state.ui_manager._render_stats_page()

    # Cleanup button
    st.markdown("---")
    if st.button("🗑️ デモデータをクリア"):
        if hasattr(st.session_state, 'temp_db_path'):
            if os.path.exists(st.session_state.temp_db_path):
                os.unlink(st.session_state.temp_db_path)

        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.success("デモデータをクリアしました。ページを再読み込みしてください。")
        st.rerun()


if __name__ == "__main__":
    main()
