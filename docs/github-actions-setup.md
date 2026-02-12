# GitHub Actions 自動同期セットアップ手順

## 概要
1時間に1回、以下のデータソースを自動同期して `context/` に保存します。

| ソース | 同期内容 | 必要なSecret |
|--------|---------|-------------|
| **Slack** | 直近3日のメッセージ | `SLACK_BOT_TOKEN`, `SLACK_CHANNELS` |
| **Google Calendar** | 今後7日の予定 | `GOOGLE_CLIENT_SECRET`, `GOOGLE_TOKEN_JSON` |
| **Notion** | 直近7日のミーティングノート | `NOTION_API_TOKEN`, `NOTION_MEETING_DB_ID` |

---

## Step 1: GitHub Secrets を設定する

リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で以下を登録します。

### Slack

| Secret名 | 値 | 取得方法 |
|----------|---|---------|
| `SLACK_BOT_TOKEN` | `xoxb-xxxx...` | [Slack API](https://api.slack.com/apps) → Your App → OAuth & Permissions → Bot User OAuth Token |
| `SLACK_CHANNELS` | `C01XXX,C02XXX` | 同期したいチャンネルIDをカンマ区切り。チャンネル名を右クリック→「リンクをコピー」でIDを確認 |

> **Bot に必要な権限 (Scopes)**: `channels:history`, `channels:read`, `groups:history`, `groups:read`

### Google Calendar

| Secret名 | 値 | 取得方法 |
|----------|---|---------|
| `GOOGLE_CLIENT_SECRET` | JSON全体 | [Google Cloud Console](https://console.cloud.google.com/) → APIとサービス → 認証情報 → OAuth 2.0 クライアント ID → JSONをダウンロード → 中身をそのまま貼り付け |
| `GOOGLE_TOKEN_JSON` | JSON全体 | ローカルの `token.json` の中身をそのまま貼り付け |

> **token.json の取得方法**: ローカルで `python scripts/calendar_sync.py` を一度実行すると、ブラウザ認証後に `token.json` が生成されます。

### Notion

| Secret名 | 値 | 取得方法 |
|----------|---|---------|
| `NOTION_API_TOKEN` | `ntn_xxxx...` | 下記「Notion Integration 作成手順」参照 |
| `NOTION_MEETING_DB_ID` | `abcd1234...` | ミーティングページのURLから取得。URLが `notion.so/xxx?v=yyy` の場合、`xxx` 部分がDB ID |

---

## Step 2: Notion Integration を作成する

1. [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) にアクセス
2. 「+ 新しいインテグレーション」をクリック
3. 設定：
   - **名前**: `CiviLink Context Sync`
   - **ワークスペース**: 株式会社MALME
   - **機能**: 「コンテンツを読み取る」のみON
4. 「送信」→ シークレットトークン (`ntn_xxx`) をコピー
5. **Notionでミーティングページにインテグレーションを接続**:
   - ミーティングページを開く
   - 右上の `...` メニュー → 「コネクト」→ 「CiviLink Context Sync」を選択

### ミーティング DB ID の確認方法

ミーティングページの「AIミーティングノート」セクションのデータベースを別ページとして開き、URLから取得します:

```
https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=yyyyyy
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      この部分がDB ID
```

---

## Step 3: 動作確認

### 手動で実行
1. GitHub リポジトリ → **Actions** タブ
2. 左メニューから「Context Sync」を選択
3. 「Run workflow」ボタンをクリック

### ログの確認
- 実行結果は Actions タブで確認できます
- 各ステップは `continue-on-error: true` なので、一部失敗しても他は実行されます
- 同期結果は `context/daily/last_sync.md` に記録されます

### cron スケジュール
- **毎時0分 (UTC)** に自動実行
- 日本時間では毎時9分頃（UTC→JST +9h）
- 変更したい場合は `.github/workflows/context-sync.yml` の `cron` を編集

---

## トラブルシューティング

### 「No changes to commit」が続く場合
- Secrets が正しく設定されているか確認
- Actions のログで各ステップのエラーメッセージを確認

### Google Calendar が認証エラーになる場合
- `token.json` の refresh_token が期限切れの可能性
- ローカルで `python scripts/calendar_sync.py` を再実行して新しい `token.json` を取得
- Secret `GOOGLE_TOKEN_JSON` を更新

### Notion が取得できない場合
- インテグレーションがミーティングページに接続されているか確認
- DB ID が正しいか確認（ハイフンなしの32文字）

---

## ファイル構成

```
.github/workflows/context-sync.yml   # GitHub Actions ワークフロー
scripts/
  slack_sync.py                       # Slack 同期スクリプト
  calendar_sync.py                    # Google Calendar 同期スクリプト
  notion_sync.py                      # Notion 同期スクリプト（新規）
  task_extractor.py                   # タスク自動抽出
requirements.txt                      # Python 依存パッケージ
```
