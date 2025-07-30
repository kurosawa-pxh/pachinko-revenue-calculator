# 勝てるクン - Streamlit Cloud デプロイメントガイド

## 概要

このガイドでは、「勝てるクン」パチンコ収支管理アプリを Streamlit Cloud に無料でデプロイする手順を説明します。

## 前提条件

- GitHub アカウント
- Supabase アカウント（無料）
- Streamlit Cloud アカウント（無料）

## デプロイメント手順

### 1. Supabase データベースセットアップ

1. [Supabase](https://supabase.com)にアクセスしてアカウント作成
2. 新しいプロジェクトを作成
3. データベース接続情報を取得：
   - Project Settings > Database > Connection string
   - パスワードを設定して URL をコピー

### 2. GitHub リポジトリ準備

1. このプロジェクトを GitHub リポジトリにプッシュ
2. リポジトリが公開されていることを確認

### 3. Streamlit Cloud デプロイ

1. [Streamlit Cloud](https://share.streamlit.io)にアクセス
2. GitHub アカウントでログイン
3. "New app"をクリック
4. リポジトリとブランチを選択
5. Main file path を `pachinko-app/app.py` に設定

### 4. 環境変数設定

Streamlit Cloud の"Advanced settings"で以下の環境変数を設定：

```toml
# 必須設定
ENVIRONMENT = "production"
DATABASE_URL = "postgresql://username:password@host:port/database"
SECRET_KEY = "your-super-secret-key-here"
ENCRYPTION_KEY = "your-32-character-encryption-key"

# オプション設定
DEBUG = "false"
LOG_LEVEL = "INFO"
ENABLE_CACHING = "true"
MAX_USERS = "100"
MAX_DB_SIZE_MB = "50"
```

### 5. デプロイメント確認

1. アプリがデプロイされるまで待機（通常 2-5 分）
2. 提供された URL でアプリにアクセス
3. ヘルスチェック機能で動作確認

## 無料枠制限

### Streamlit Cloud 制限

- 1 つのアプリあたり 1GB RAM
- 1 つのアプリあたり 1 CPU
- 月間 100 時間の実行時間
- 3 つまでのプライベートアプリ

### Supabase 制限

- 500MB ストレージ
- 月間 2GB 帯域幅
- 最大 50MB データベースサイズ
- 100 同時接続

## 監視とメンテナンス

### リソース使用量監視

アプリ内の「📊 リソース使用状況」セクションで以下を監視：

- ユーザー数
- セッション数
- データベースサイズ
- 帯域幅使用量

### ログ監視

Streamlit Cloud のログで以下を確認：

- エラーメッセージ
- パフォーマンス問題
- セキュリティアラート

### 定期メンテナンス

1. **週次**：

   - リソース使用量確認
   - エラーログ確認
   - パフォーマンス確認

2. **月次**：
   - データベースバックアップ
   - セキュリティ更新確認
   - 無料枠使用量確認

## トラブルシューティング

### よくある問題

1. **データベース接続エラー**

   - DATABASE_URL が正しく設定されているか確認
   - Supabase プロジェクトが有効か確認
   - パスワードに特殊文字が含まれていないか確認

2. **メモリ不足エラー**

   - キャッシュ設定を確認
   - 大量データの処理を最適化
   - セッション状態の管理を見直し

3. **認証エラー**
   - SECRET_KEY が設定されているか確認
   - ENCRYPTION_KEY が 32 文字であることを確認
   - セッションタイムアウト設定を確認

### デバッグ方法

1. **ローカルでのテスト**：

   ```bash
   cd pachinko-app
   streamlit run app.py
   ```

2. **環境変数の確認**：

   ```python
   import os
   print(os.getenv('DATABASE_URL'))  # マスクされた値が表示される
   ```

3. **ヘルスチェック**：
   アプリ内の管理画面でシステム状態を確認

## セキュリティ考慮事項

1. **環境変数**：

   - 本番環境では必ず強力な SECRET_KEY を使用
   - ENCRYPTION_KEY は 32 文字のランダム文字列を使用
   - データベースパスワードは複雑なものを使用

2. **アクセス制御**：

   - 認証機能を有効化
   - セッションタイムアウトを適切に設定
   - 不正アクセス検出を有効化

3. **データ保護**：
   - データベース暗号化を有効化
   - HTTPS 通信の確認
   - 定期的なバックアップ

## パフォーマンス最適化

1. **キャッシュ活用**：

   - `@st.cache_data`を適切に使用
   - セッション状態の効率的な管理
   - データベースクエリの最適化

2. **リソース管理**：

   - 不要なデータの定期削除
   - 画像サイズの最適化
   - メモリ使用量の監視

3. **ユーザーエクスペリエンス**：
   - ローディング表示の実装
   - エラーハンドリングの改善
   - レスポンシブデザインの確認

## サポート

問題が発生した場合：

1. まずこのガイドのトラブルシューティングセクションを確認
2. Streamlit Cloud のドキュメントを参照
3. Supabase のドキュメントを参照
4. GitHub の Issues で報告

## 更新とアップグレード

1. **コード更新**：

   - GitHub にプッシュすると自動的にデプロイ
   - 重要な変更前はローカルでテスト

2. **依存関係更新**：

   - requirements.txt の更新
   - セキュリティアップデートの適用

3. **設定変更**：
   - 環境変数の更新
   - Streamlit 設定の調整
