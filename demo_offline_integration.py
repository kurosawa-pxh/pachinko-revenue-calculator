"""
オフライン機能のデモンストレーション
ローカルストレージへのデータ保存とネットワーク復旧時の同期機能をデモ
"""

from src.models import GameSession
from src.database import DatabaseManager
from src.offline import OfflineStorageManager
import sys
import os
from datetime import datetime
from unittest.mock import Mock

# パスを追加してモジュールをインポート
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def demo_offline_functionality():
    """オフライン機能のデモンストレーション"""
    print("=" * 60)
    print("🎰 パチンコ収支管理アプリ - オフライン機能デモ")
    print("=" * 60)

    # DatabaseManagerのモックを作成
    mock_db_manager = Mock(spec=DatabaseManager)
    mock_db_manager.create_session.return_value = 100
    mock_db_manager.update_session.return_value = True

    # OfflineStorageManagerを初期化
    offline_manager = OfflineStorageManager(mock_db_manager)

    print("\n1. オフライン状態でのデータ保存テスト")
    print("-" * 40)

    # テスト用のセッションデータを作成
    session_data_1 = {
        'user_id': 'demo_user',
        'date': '2024-01-15',
        'start_time': '2024-01-15T10:00:00',
        'store_name': 'パチンコ太郎',
        'machine_name': 'CR花の慶次',
        'initial_investment': 10000,
        'created_at': '2024-01-15T10:00:00',
        'updated_at': '2024-01-15T10:00:00'
    }

    session_data_2 = {
        'user_id': 'demo_user',
        'date': '2024-01-15',
        'start_time': '2024-01-15T14:00:00',
        'end_time': '2024-01-15T16:00:00',
        'store_name': 'パチンコ花子',
        'machine_name': 'CRぱちんこ必殺仕事人',
        'initial_investment': 15000,
        'final_investment': 20000,
        'return_amount': 25000,
        'profit': 5000,
        'is_completed': True,
        'created_at': '2024-01-15T14:00:00',
        'updated_at': '2024-01-15T16:00:00'
    }

    # オフライン状態でデータを保存
    print("📱 セッション1をローカルストレージに保存中...")
    result1 = offline_manager.save_to_local_storage(session_data_1)
    print(f"   結果: {'✅ 成功' if result1 else '❌ 失敗'}")

    print("📱 セッション2をローカルストレージに保存中...")
    result2 = offline_manager.save_to_local_storage(session_data_2)
    print(f"   結果: {'✅ 成功' if result2 else '❌ 失敗'}")

    print("\n2. ローカルストレージからのデータ読み込み")
    print("-" * 40)

    # ローカルストレージからデータを読み込み
    local_data = offline_manager.load_from_local_storage()
    if local_data:
        print(f"📂 ローカルデータが見つかりました")
        print(f"   セッション数: {len(local_data.get('sessions', {}))}")
        print(f"   最終更新: {local_data.get('last_updated', 'N/A')}")
    else:
        print("❌ ローカルデータが見つかりません")

    print("\n3. 同期待ちセッションの確認")
    print("-" * 40)

    # 同期待ちセッションを取得
    pending_sessions = offline_manager.get_pending_sessions()
    print(f"⏳ 同期待ちセッション数: {len(pending_sessions)}")

    for i, session in enumerate(pending_sessions, 1):
        print(f"   セッション{i}:")
        print(f"     店舗: {session.get('store_name', 'N/A')}")
        print(f"     機種: {session.get('machine_name', 'N/A')}")
        print(f"     投資額: {session.get('initial_investment', 0):,}円")
        if session.get('profit'):
            profit_color = "💰" if session['profit'] > 0 else "💸"
            print(f"     収支: {profit_color} {session['profit']:+,}円")

    print("\n4. ネットワーク状態の確認")
    print("-" * 40)

    # ネットワーク状態を確認（実際のネットワークチェック）
    network_status = offline_manager.detect_network_status()
    print(f"🌐 ネットワーク状態: {'🟢 オンライン' if network_status else '🔴 オフライン'}")

    print("\n5. オフライン状態の詳細情報")
    print("-" * 40)

    # オフライン状態の詳細を取得
    offline_status = offline_manager.get_offline_status()
    print(f"📊 オフライン状態:")
    print(
        f"   ローカルデータ有無: {'✅ あり' if offline_status['has_local_data'] else '❌ なし'}")
    print(f"   同期待ち件数: {offline_status['pending_sync_count']}件")
    print(
        f"   ネットワーク接続: {'✅ 可能' if offline_status['network_available'] else '❌ 不可'}")
    print(f"   最終更新: {offline_status.get('last_updated', 'N/A')}")

    print("\n6. サーバーとの同期テスト")
    print("-" * 40)

    if network_status:
        print("🔄 サーバーとの同期を開始...")
        sync_result = offline_manager.sync_with_server()
        print(f"   同期結果: {'✅ 成功' if sync_result else '❌ 失敗'}")

        if sync_result:
            print(
                f"   データベース保存回数: {mock_db_manager.create_session.call_count}")

            # 同期後の状態を確認
            remaining_pending = offline_manager.get_pending_sessions()
            print(f"   同期後の待機セッション数: {len(remaining_pending)}")
    else:
        print("🔴 ネットワーク接続がないため、同期をスキップします")
        print("   ネットワーク復旧後に自動同期されます")

    print("\n7. データ競合処理のデモ")
    print("-" * 40)

    # データ競合のシミュレーション
    local_data_conflict = {
        'id': 1,
        'updated_at': '2024-01-15T12:00:00',
        'data': 'ローカルで更新されたデータ',
        'profit': 5000
    }

    server_data_conflict = {
        'id': 1,
        'updated_at': '2024-01-15T11:30:00',
        'data': 'サーバーのデータ',
        'profit': 3000
    }

    print("⚡ データ競合が発生した場合の処理:")
    print(f"   ローカル更新時刻: {local_data_conflict['updated_at']}")
    print(f"   サーバー更新時刻: {server_data_conflict['updated_at']}")

    resolved_data = offline_manager.handle_data_conflicts(
        local_data_conflict, server_data_conflict)
    print(f"   採用されたデータ: {resolved_data['data']}")
    print(
        f"   理由: {'ローカルデータが新しいため' if resolved_data == local_data_conflict else 'サーバーデータが新しいため'}")

    print("\n8. ローカルストレージのクリア")
    print("-" * 40)

    print("🗑️  ローカルストレージをクリア中...")
    clear_result = offline_manager.clear_local_storage()
    print(f"   結果: {'✅ 成功' if clear_result else '❌ 失敗'}")

    # クリア後の状態確認
    final_data = offline_manager.load_from_local_storage()
    print(f"   クリア後のデータ: {'❌ なし' if final_data is None else '⚠️  まだ残っている'}")

    print("\n" + "=" * 60)
    print("🎉 オフライン機能デモが完了しました！")
    print("=" * 60)

    print("\n📋 機能まとめ:")
    print("✅ ローカルストレージへのデータ保存")
    print("✅ オフライン状態でのデータ管理")
    print("✅ ネットワーク状態の自動検出")
    print("✅ ネットワーク復旧時の自動同期")
    print("✅ データ競合の自動解決")
    print("✅ 同期状態の詳細管理")

    print("\n🎯 要件達成状況:")
    print("✅ 要件4.3: オフライン状態でのローカルストレージ保存")
    print("✅ 要件4.4: ネットワーク復旧時のサーバー同期")


if __name__ == "__main__":
    demo_offline_functionality()
