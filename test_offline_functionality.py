"""
オフライン機能のテスト
ローカルストレージへのデータ保存とネットワーク復旧時の同期機能をテスト
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

# テスト対象のモジュールをインポート
from src.offline import OfflineStorageManager
from src.models import GameSession
from src.database import DatabaseManager


class TestOfflineStorageManager:
    """OfflineStorageManagerのテストクラス"""

    @pytest.fixture
    def mock_db_manager(self):
        """DatabaseManagerのモックを作成"""
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def offline_manager(self, mock_db_manager):
        """OfflineStorageManagerのインスタンスを作成"""
        return OfflineStorageManager(mock_db_manager)

    @pytest.fixture
    def sample_session_data(self):
        """テスト用のサンプルセッションデータ"""
        return {
            'id': 1,
            'user_id': 'test_user',
            'date': '2024-01-15',
            'start_time': '2024-01-15T10:00:00',
            'end_time': '2024-01-15T12:00:00',
            'store_name': 'テスト店舗',
            'machine_name': 'テスト機種',
            'initial_investment': 10000,
            'final_investment': 15000,
            'return_amount': 20000,
            'profit': 5000,
            'is_completed': True,
            'created_at': '2024-01-15T10:00:00',
            'updated_at': '2024-01-15T12:00:00'
        }

    @patch('streamlit.session_state', {})
    def test_save_to_local_storage_success(self, offline_manager, sample_session_data):
        """ローカルストレージへの保存が成功することをテスト"""
        # テスト実行
        result = offline_manager.save_to_local_storage(sample_session_data)

        # 検証
        assert result is True
        assert offline_manager.local_storage_key in st.session_state

        # 保存されたデータを確認
        saved_data = json.loads(
            st.session_state[offline_manager.local_storage_key])
        assert 'sessions' in saved_data
        assert str(sample_session_data['id']) in saved_data['sessions']
        assert saved_data['sessions'][str(
            sample_session_data['id'])]['sync_status'] == 'pending'
        assert 'offline_timestamp' in saved_data['sessions'][str(
            sample_session_data['id'])]

    @patch('streamlit.session_state', {})
    def test_save_to_local_storage_new_session(self, offline_manager):
        """新しいセッション（IDなし）の保存をテスト"""
        session_data = {
            'user_id': 'test_user',
            'date': '2024-01-15',
            'start_time': '2024-01-15T10:00:00',
            'store_name': 'テスト店舗',
            'machine_name': 'テスト機種',
            'initial_investment': 10000,
            'created_at': '2024-01-15T10:00:00',
            'updated_at': '2024-01-15T10:00:00'
        }

        # テスト実行
        result = offline_manager.save_to_local_storage(session_data)

        # 検証
        assert result is True
        saved_data = json.loads(
            st.session_state[offline_manager.local_storage_key])

        # オフラインIDが生成されていることを確認
        session_ids = list(saved_data['sessions'].keys())
        assert len(session_ids) == 1
        assert session_ids[0].startswith('offline_')

    @patch('streamlit.session_state', {})
    def test_load_from_local_storage_empty(self, offline_manager):
        """空のローカルストレージからの読み込みをテスト"""
        result = offline_manager.load_from_local_storage()
        assert result is None

    @patch('streamlit.session_state')
    def test_load_from_local_storage_with_data(self, mock_session_state, offline_manager, sample_session_data):
        """データが存在するローカルストレージからの読み込みをテスト"""
        # テストデータを準備
        test_data = {
            'sessions': {
                '1': sample_session_data
            },
            'last_updated': '2024-01-15T12:00:00'
        }
        mock_session_state.__contains__.return_value = True
        mock_session_state.__getitem__.return_value = json.dumps(test_data)

        # テスト実行
        result = offline_manager.load_from_local_storage()

        # 検証
        assert result is not None
        assert 'sessions' in result
        assert '1' in result['sessions']
        assert result['sessions']['1']['user_id'] == 'test_user'

    @patch('streamlit.session_state')
    def test_get_pending_sessions(self, mock_session_state, offline_manager, sample_session_data):
        """同期待ちセッションの取得をテスト"""
        # テストデータを準備（同期待ちと同期済みのセッション）
        pending_session = sample_session_data.copy()
        pending_session['sync_status'] = 'pending'

        synced_session = sample_session_data.copy()
        synced_session['id'] = 2
        synced_session['sync_status'] = 'synced'

        test_data = {
            'sessions': {
                '1': pending_session,
                '2': synced_session
            }
        }
        mock_session_state.__contains__.return_value = True
        mock_session_state.__getitem__.return_value = json.dumps(test_data)

        # テスト実行
        result = offline_manager.get_pending_sessions()

        # 検証
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['sync_status'] == 'pending'

    @patch('requests.get')
    def test_detect_network_status_online(self, mock_get, offline_manager):
        """ネットワーク接続状態（オンライン）の検出をテスト"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # テスト実行
        result = offline_manager.detect_network_status()

        # 検証
        assert result is True
        mock_get.assert_called_once_with(
            'https://httpbin.org/status/200', timeout=5)

    @patch('requests.get')
    def test_detect_network_status_offline(self, mock_get, offline_manager):
        """ネットワーク接続状態（オフライン）の検出をテスト"""
        # ネットワークエラーをシミュレート
        mock_get.side_effect = Exception("Network error")

        # テスト実行
        result = offline_manager.detect_network_status()

        # 検証
        assert result is False

    @patch('streamlit.session_state')
    def test_sync_with_server_no_network(self, mock_session_state, offline_manager):
        """ネットワーク接続なしでの同期をテスト"""
        with patch.object(offline_manager, 'detect_network_status', return_value=False):
            result = offline_manager.sync_with_server()
            assert result is False

    @patch('streamlit.session_state')
    def test_sync_with_server_no_pending_data(self, mock_session_state, offline_manager):
        """同期待ちデータなしでの同期をテスト"""
        with patch.object(offline_manager, 'detect_network_status', return_value=True):
            with patch.object(offline_manager, 'get_pending_sessions', return_value=[]):
                result = offline_manager.sync_with_server()
                assert result is True

    @patch('streamlit.session_state', {})
    def test_sync_with_server_success(self, offline_manager, sample_session_data, mock_db_manager):
        """同期成功のテスト"""
        # テストデータを準備
        pending_session = sample_session_data.copy()
        pending_session['id'] = 'offline_123456789'
        pending_session['sync_status'] = 'pending'

        # ローカルストレージにデータを保存
        offline_manager.save_to_local_storage(pending_session)

        # モックを設定
        mock_db_manager.create_session.return_value = 100  # 新しいサーバーID

        with patch.object(offline_manager, 'detect_network_status', return_value=True):
            with patch.object(offline_manager, '_cleanup_synced_data'):
                result = offline_manager.sync_with_server()

                # 検証
                assert result is True
                mock_db_manager.create_session.assert_called_once()

    def test_handle_data_conflicts_local_newer(self, offline_manager):
        """データ競合処理（ローカルが新しい）をテスト"""
        local_data = {
            'updated_at': '2024-01-15T12:00:00',
            'data': 'local'
        }
        server_data = {
            'updated_at': '2024-01-15T11:00:00',
            'data': 'server'
        }

        result = offline_manager.handle_data_conflicts(local_data, server_data)
        assert result['data'] == 'local'

    def test_handle_data_conflicts_server_newer(self, offline_manager):
        """データ競合処理（サーバーが新しい）をテスト"""
        local_data = {
            'updated_at': '2024-01-15T11:00:00',
            'data': 'local'
        }
        server_data = {
            'updated_at': '2024-01-15T12:00:00',
            'data': 'server'
        }

        result = offline_manager.handle_data_conflicts(local_data, server_data)
        assert result['data'] == 'server'

    def test_dict_to_game_session(self, offline_manager, sample_session_data):
        """辞書からGameSessionオブジェクトへの変換をテスト"""
        result = offline_manager._dict_to_game_session(sample_session_data)

        assert isinstance(result, GameSession)
        assert result.id == sample_session_data['id']
        assert result.user_id == sample_session_data['user_id']
        assert result.store_name == sample_session_data['store_name']
        assert result.machine_name == sample_session_data['machine_name']
        assert result.initial_investment == sample_session_data['initial_investment']
        assert result.profit == sample_session_data['profit']

    @patch('streamlit.session_state')
    def test_get_offline_status(self, mock_session_state, offline_manager):
        """オフライン状態の取得をテスト"""
        # モックを設定
        mock_session_state.__contains__.return_value = True
        mock_session_state.__getitem__.return_value = json.dumps({
            'sessions': {'1': {'sync_status': 'pending'}},
            'last_updated': '2024-01-15T12:00:00'
        })

        with patch.object(offline_manager, 'detect_network_status', return_value=True):
            result = offline_manager.get_offline_status()

            assert result['has_local_data'] is True
            assert result['pending_sync_count'] == 1
            assert result['network_available'] is True
            assert result['last_updated'] == '2024-01-15T12:00:00'

    @patch('streamlit.session_state', {})
    def test_clear_local_storage(self, offline_manager):
        """ローカルストレージのクリアをテスト"""
        # データを保存
        st.session_state[offline_manager.local_storage_key] = "test_data"
        st.session_state[offline_manager.sync_status_key] = "test_status"

        # クリア実行
        result = offline_manager.clear_local_storage()

        # 検証
        assert result is True
        assert offline_manager.local_storage_key not in st.session_state
        assert offline_manager.sync_status_key not in st.session_state


class TestOfflineIntegration:
    """オフライン機能の統合テスト"""

    @pytest.fixture
    def mock_db_manager(self):
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def offline_manager(self, mock_db_manager):
        return OfflineStorageManager(mock_db_manager)

    @patch('streamlit.session_state', {})
    def test_complete_offline_workflow(self, offline_manager, mock_db_manager):
        """完全なオフラインワークフローをテスト"""
        # 1. オフライン状態でデータを保存
        session_data = {
            'user_id': 'test_user',
            'date': '2024-01-15',
            'start_time': '2024-01-15T10:00:00',
            'store_name': 'テスト店舗',
            'machine_name': 'テスト機種',
            'initial_investment': 10000,
            'created_at': '2024-01-15T10:00:00',
            'updated_at': '2024-01-15T10:00:00'
        }

        # データ保存
        save_result = offline_manager.save_to_local_storage(session_data)
        assert save_result is True

        # 2. 同期待ちデータの確認
        pending_sessions = offline_manager.get_pending_sessions()
        assert len(pending_sessions) == 1
        assert pending_sessions[0]['sync_status'] == 'pending'

        # 3. ネットワーク復旧後の同期
        mock_db_manager.create_session.return_value = 200

        with patch.object(offline_manager, 'detect_network_status', return_value=True):
            with patch.object(offline_manager, '_cleanup_synced_data'):
                sync_result = offline_manager.sync_with_server()
                assert sync_result is True

        # 4. データベースへの保存が呼ばれたことを確認
        mock_db_manager.create_session.assert_called_once()

    @patch('streamlit.session_state', {})
    def test_multiple_sessions_sync(self, offline_manager, mock_db_manager):
        """複数セッションの同期をテスト"""
        # 複数のセッションを保存
        for i in range(3):
            session_data = {
                'user_id': 'test_user',
                'date': f'2024-01-{15+i}',
                'start_time': f'2024-01-{15+i}T10:00:00',
                'store_name': f'テスト店舗{i}',
                'machine_name': f'テスト機種{i}',
                'initial_investment': 10000 + i * 1000,
                'created_at': f'2024-01-{15+i}T10:00:00',
                'updated_at': f'2024-01-{15+i}T10:00:00'
            }
            offline_manager.save_to_local_storage(session_data)

        # 同期待ちセッション数を確認
        pending_sessions = offline_manager.get_pending_sessions()
        assert len(pending_sessions) == 3

        # 同期実行
        mock_db_manager.create_session.return_value = 300

        with patch.object(offline_manager, 'detect_network_status', return_value=True):
            with patch.object(offline_manager, '_cleanup_synced_data'):
                sync_result = offline_manager.sync_with_server()
                assert sync_result is True

        # 3回のデータベース保存が呼ばれたことを確認
        assert mock_db_manager.create_session.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
