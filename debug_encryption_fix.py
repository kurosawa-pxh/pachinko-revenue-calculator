#!/usr/bin/env python3
"""
暗号化データの復号化問題をデバッグ・修正するスクリプト
"""

from src.config import get_config
from src.authentication import AuthenticationManager
from src.database import DatabaseManager
import sys
import os
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def debug_encryption_issue():
    """暗号化データの問題をデバッグする"""
    print("🔍 暗号化データの復号化問題をデバッグ中...")

    try:
        # 認証マネージャーを初期化
        print("1. 認証マネージャーを初期化中...")
        auth_manager = AuthenticationManager(
            db_path="pachinko_auth.db"
        )
        print("✅ 認証マネージャー初期化完了")

        # データベースマネージャーを初期化
        print("2. データベースマネージャーを初期化中...")
        config = get_config()
        db_manager = DatabaseManager(
            encryption_manager=auth_manager,
            config=config
        )
        print("✅ データベースマネージャー初期化完了")

        # 暗号化マネージャーが正しく設定されているかチェック
        print("3. 暗号化マネージャーの設定をチェック中...")
        if db_manager.encryption_manager:
            print("✅ 暗号化マネージャーが設定されています")
        else:
            print("❌ 暗号化マネージャーが設定されていません")
            return False

        # テストユーザーのセッションデータを取得
        print("4. セッションデータを取得中...")
        user_id = "1"  # デフォルトユーザー
        sessions = db_manager.get_sessions(user_id, limit=5)

        if not sessions:
            print("ℹ️ セッションデータが見つかりません")
            return True

        print(f"📊 {len(sessions)}件のセッションを取得しました")

        # 各セッションの暗号化状態をチェック
        print("5. セッションデータの暗号化状態をチェック中...")
        for i, session in enumerate(sessions):
            print(f"\n--- セッション {i+1} ---")
            print(f"ID: {session.id}")
            print(f"日付: {session.date}")
            print(f"店舗名: {session.store_name}")
            print(f"機種名: {session.machine_name}")

            # 暗号化されているかチェック
            store_encrypted = db_manager._is_encrypted_data(session.store_name)
            machine_encrypted = db_manager._is_encrypted_data(
                session.machine_name)

            print(f"店舗名暗号化: {'はい' if store_encrypted else 'いいえ'}")
            print(f"機種名暗号化: {'はい' if machine_encrypted else 'いいえ'}")

            if store_encrypted or machine_encrypted:
                print("⚠️ 暗号化されたデータが検出されました")

                # 手動で復号化を試行
                try:
                    if store_encrypted:
                        decrypted_store = auth_manager.decrypt_data(
                            session.store_name)
                        print(f"復号化された店舗名: {decrypted_store}")

                    if machine_encrypted:
                        decrypted_machine = auth_manager.decrypt_data(
                            session.machine_name)
                        print(f"復号化された機種名: {decrypted_machine}")

                    print("✅ 復号化成功")

                except Exception as e:
                    print(f"❌ 復号化失敗: {e}")
            else:
                print("✅ データは既に復号化されています")

        print("\n🎯 デバッグ完了")
        return True

    except Exception as e:
        print(f"❌ デバッグ中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def fix_encryption_display():
    """暗号化表示の問題を修正する"""
    print("\n🔧 暗号化表示の問題を修正中...")

    try:
        # 認証マネージャーを初期化
        auth_manager = AuthenticationManager(db_path="pachinko_auth.db")

        # データベースマネージャーを初期化
        config = get_config()
        db_manager = DatabaseManager(
            encryption_manager=auth_manager,
            config=config
        )

        # 暗号化マネージャーが設定されていることを確認
        if not db_manager.encryption_manager:
            print("❌ 暗号化マネージャーが設定されていません")
            return False

        # すべてのセッションを取得して復号化状態をチェック
        user_id = "1"
        sessions_dict = db_manager.get_sessions_as_dict(user_id, limit=10)

        print(f"📊 {len(sessions_dict)}件のセッションをチェック中...")

        fixed_count = 0
        for session_data in sessions_dict:
            store_name = session_data.get('store_name', '')
            machine_name = session_data.get('machine_name', '')

            # 暗号化されているかチェック
            if db_manager._is_encrypted_data(store_name) or db_manager._is_encrypted_data(machine_name):
                print(f"🔓 セッション ID {session_data.get('id')} の暗号化データを検出")
                fixed_count += 1

        if fixed_count > 0:
            print(f"✅ {fixed_count}件の暗号化データが検出されました")
            print("💡 データベースマネージャーの復号化処理が正しく動作するはずです")
        else:
            print("ℹ️ 暗号化されたデータは見つかりませんでした")

        return True

    except Exception as e:
        print(f"❌ 修正中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン関数"""
    print("🎰 パチンコアプリ暗号化デバッグツール")
    print("=" * 50)

    # ログレベルを設定
    logging.basicConfig(level=logging.WARNING)

    # デバッグ実行
    debug_success = debug_encryption_issue()

    if debug_success:
        # 修正実行
        fix_success = fix_encryption_display()

        if fix_success:
            print("\n🎉 暗号化データの問題が修正されました！")
            print("💡 アプリケーションを再起動してダッシュボードを確認してください")
        else:
            print("\n❌ 修正に失敗しました")
    else:
        print("\n❌ デバッグに失敗しました")


if __name__ == "__main__":
    main()
