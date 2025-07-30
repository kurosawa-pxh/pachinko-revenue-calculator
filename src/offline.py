"""
オフライン対応機能の実装
ローカルストレージへのデータ保存とネットワーク復旧時の同期機能を提供
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st
import requests
from .models import GameSession
from .database import DatabaseManager


class OfflineStorageManager:
    """
    オフライン機能を管理するクラス
    ブラウザのlocalStorageを活用してオフライン状態でもアプリケーションを使用可能にする
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        self.local_storage_key = "pachinko_offline_data"
        self.sync_status_key = "pachinko_sync_status"

    def save_to_local_storage(self, data: Dict[str, Any]) -> bool:
        """
        データをローカルストレージに保存

        Args:
            data: 保存するデータ（辞書形式）

        Returns:
            bool: 保存成功時True、失敗時False
        """
        try:
            # 現在のローカルデータを取得
            current_data = self.load_from_local_storage() or {}

            # タイムスタンプを追加
            data['offline_timestamp'] = datetime.now().isoformat()
            data['sync_status'] = 'pending'

            # セッションIDをキーとして保存
            if 'sessions' not in current_data:
                current_data['sessions'] = {}

            # 新しいセッションの場合、一意のIDを生成
            if 'id' not in data or data['id'] is None:
                import random
                data['id'] = f"offline_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

            current_data['sessions'][str(data['id'])] = data
            current_data['last_updated'] = datetime.now().isoformat()

            # Streamlitのセッション状態に保存（localStorage代替）
            st.session_state[self.local_storage_key] = json.dumps(current_data)

            self.logger.info(f"データをローカルストレージに保存しました: {data['id']}")
            return True

        except Exception as e:
            self.logger.error(f"ローカルストレージへの保存に失敗しました: {e}")
            return False

    def load_from_local_storage(self) -> Optional[Dict[str, Any]]:
        """
        ローカルストレージからデータを読み込み

        Returns:
            Optional[Dict]: 読み込んだデータ、失敗時はNone
        """
        try:
            # Streamlitのセッション状態から読み込み
            if self.local_storage_key in st.session_state:
                data_str = st.session_state[self.local_storage_key]
                data = json.loads(data_str)
                self.logger.info("ローカルストレージからデータを読み込みました")
                return data
            else:
                self.logger.info("ローカルストレージにデータが存在しません")
                return None

        except Exception as e:
            self.logger.error(f"ローカルストレージからの読み込みに失敗しました: {e}")
            return None

    def get_pending_sessions(self) -> List[Dict[str, Any]]:
        """
        同期待ちのセッションデータを取得

        Returns:
            List[Dict]: 同期待ちのセッションリスト
        """
        try:
            local_data = self.load_from_local_storage()
            if not local_data or 'sessions' not in local_data:
                return []

            pending_sessions = []
            for session_id, session_data in local_data['sessions'].items():
                if session_data.get('sync_status') == 'pending':
                    pending_sessions.append(session_data)

            return pending_sessions

        except Exception as e:
            self.logger.error(f"同期待ちセッションの取得に失敗しました: {e}")
            return []

    def sync_with_server(self) -> bool:
        """
        ローカルデータをサーバーと同期

        Returns:
            bool: 同期成功時True、失敗時False
        """
        try:
            if not self.detect_network_status():
                self.logger.warning("ネットワーク接続がありません。同期をスキップします。")
                return False

            pending_sessions = self.get_pending_sessions()
            if not pending_sessions:
                self.logger.info("同期待ちのデータがありません")
                return True

            sync_success_count = 0
            sync_error_count = 0

            for session_data in pending_sessions:
                try:
                    # GameSessionオブジェクトに変換
                    game_session = self._dict_to_game_session(session_data)

                    # データベースに保存
                    if game_session.id and str(game_session.id).startswith('offline_'):
                        # オフラインで作成されたセッションの場合、新規作成
                        session_dict = game_session.to_dict()
                        session_dict.pop('id', None)  # IDを削除して新規作成
                        new_id = self.db_manager.create_session(session_dict)
                        if new_id:
                            # ローカルストレージの同期ステータスを更新
                            self._update_sync_status(
                                session_data['id'], 'synced', new_id)
                            sync_success_count += 1
                        else:
                            sync_error_count += 1
                    else:
                        # 既存セッションの更新
                        success = self.db_manager.update_session(
                            game_session.id,
                            game_session.to_dict()
                        )
                        if success:
                            self._update_sync_status(
                                session_data['id'], 'synced')
                            sync_success_count += 1
                        else:
                            sync_error_count += 1

                except Exception as e:
                    self.logger.error(f"セッション同期エラー: {e}")
                    sync_error_count += 1

            self.logger.info(
                f"同期完了: 成功 {sync_success_count}件, エラー {sync_error_count}件")

            # 同期完了後、成功したデータをローカルストレージから削除
            if sync_success_count > 0:
                self._cleanup_synced_data()

            return sync_error_count == 0

        except Exception as e:
            self.logger.error(f"サーバー同期に失敗しました: {e}")
            return False

    def detect_network_status(self) -> bool:
        """
        ネットワーク接続状態を検出

        Returns:
            bool: 接続可能時True、不可能時False
        """
        try:
            # 簡単なHTTPリクエストでネットワーク状態を確認
            response = requests.get(
                'https://httpbin.org/status/200', timeout=5)
            return response.status_code == 200
        except:
            # ネットワークエラーの場合はオフライン状態と判断
            return False

    def handle_data_conflicts(self, local_data: Dict[str, Any], server_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        ローカルデータとサーバーデータの競合を処理

        Args:
            local_data: ローカルデータ
            server_data: サーバーデータ

        Returns:
            Dict: 競合解決後のデータ
        """
        try:
            # タイムスタンプベースの競合解決
            local_timestamp = datetime.fromisoformat(
                local_data.get('updated_at', '1970-01-01'))
            server_timestamp = datetime.fromisoformat(
                server_data.get('updated_at', '1970-01-01'))

            if local_timestamp > server_timestamp:
                self.logger.info("ローカルデータが新しいため、ローカルデータを採用")
                return local_data
            else:
                self.logger.info("サーバーデータが新しいため、サーバーデータを採用")
                return server_data

        except Exception as e:
            self.logger.error(f"データ競合の解決に失敗しました: {e}")
            # エラーの場合はサーバーデータを優先
            return server_data

    def _dict_to_game_session(self, data: Dict[str, Any]) -> GameSession:
        """
        辞書データをGameSessionオブジェクトに変換

        Args:
            data: 辞書形式のセッションデータ

        Returns:
            GameSession: 変換されたGameSessionオブジェクト
        """
        # 日付文字列をdatetimeオブジェクトに変換
        date = datetime.fromisoformat(data['date']) if isinstance(
            data['date'], str) else data['date']
        start_time = datetime.fromisoformat(data['start_time']) if isinstance(
            data['start_time'], str) else data['start_time']
        end_time = None
        if data.get('end_time'):
            end_time = datetime.fromisoformat(data['end_time']) if isinstance(
                data['end_time'], str) else data['end_time']

        created_at = datetime.fromisoformat(data['created_at']) if isinstance(
            data['created_at'], str) else data['created_at']
        updated_at = datetime.fromisoformat(data['updated_at']) if isinstance(
            data['updated_at'], str) else data['updated_at']

        return GameSession(
            id=data.get('id'),
            user_id=data['user_id'],
            date=date,
            start_time=start_time,
            end_time=end_time,
            store_name=data['store_name'],
            machine_name=data['machine_name'],
            initial_investment=data['initial_investment'],
            final_investment=data.get('final_investment'),
            return_amount=data.get('return_amount'),
            profit=data.get('profit'),
            is_completed=data.get('is_completed', False),
            created_at=created_at,
            updated_at=updated_at
        )

    def _update_sync_status(self, session_id: str, status: str, new_id: Optional[int] = None):
        """
        ローカルストレージの同期ステータスを更新

        Args:
            session_id: セッションID
            status: 新しいステータス
            new_id: 新しいサーバーID（オプション）
        """
        try:
            local_data = self.load_from_local_storage()
            if local_data and 'sessions' in local_data:
                if str(session_id) in local_data['sessions']:
                    local_data['sessions'][str(
                        session_id)]['sync_status'] = status
                    if new_id:
                        local_data['sessions'][str(
                            session_id)]['server_id'] = new_id

                    st.session_state[self.local_storage_key] = json.dumps(
                        local_data)

        except Exception as e:
            self.logger.error(f"同期ステータスの更新に失敗しました: {e}")

    def _cleanup_synced_data(self):
        """
        同期完了したデータをローカルストレージから削除
        """
        try:
            local_data = self.load_from_local_storage()
            if not local_data or 'sessions' not in local_data:
                return

            # 同期完了したセッションを削除
            sessions_to_remove = []
            for session_id, session_data in local_data['sessions'].items():
                if session_data.get('sync_status') == 'synced':
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del local_data['sessions'][session_id]

            # 更新されたデータを保存
            st.session_state[self.local_storage_key] = json.dumps(local_data)

            self.logger.info(f"同期完了データを削除しました: {len(sessions_to_remove)}件")

        except Exception as e:
            self.logger.error(f"同期完了データの削除に失敗しました: {e}")

    def get_offline_status(self) -> Dict[str, Any]:
        """
        オフライン機能の状態を取得

        Returns:
            Dict: オフライン状態の情報
        """
        try:
            local_data = self.load_from_local_storage()
            pending_count = len(self.get_pending_sessions())
            network_status = self.detect_network_status()

            return {
                'has_local_data': local_data is not None,
                'pending_sync_count': pending_count,
                'network_available': network_status,
                'last_sync': local_data.get('last_sync') if local_data else None,
                'last_updated': local_data.get('last_updated') if local_data else None
            }

        except Exception as e:
            self.logger.error(f"オフライン状態の取得に失敗しました: {e}")
            return {
                'has_local_data': False,
                'pending_sync_count': 0,
                'network_available': False,
                'last_sync': None,
                'last_updated': None
            }

    def clear_local_storage(self) -> bool:
        """
        ローカルストレージをクリア

        Returns:
            bool: クリア成功時True
        """
        try:
            if self.local_storage_key in st.session_state:
                del st.session_state[self.local_storage_key]
            if self.sync_status_key in st.session_state:
                del st.session_state[self.sync_status_key]

            self.logger.info("ローカルストレージをクリアしました")
            return True

        except Exception as e:
            self.logger.error(f"ローカルストレージのクリアに失敗しました: {e}")
            return False
