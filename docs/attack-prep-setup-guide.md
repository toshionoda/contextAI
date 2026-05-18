# /attack-prep セットアップガイド

顧客アタック前のブリーフィングを自動生成するClaude Codeスキルの導入手順です。
`/attack-prep 九州 pckk` のように実行すると、Mazrica・Slack・Notionから情報を一括収集してブリーフィングを出力します。

---

## 前提条件

- macOS（Apple Silicon / Intel）
- Git でこのリポジトリ（contextAI）にアクセスできること
- Anthropic のアカウント（Claude Pro / Team / Enterprise いずれか）

---

## Step 1: Claude Code のインストール

```bash
# npm でインストール（Node.js 18+ が必要）
npm install -g @anthropic-ai/claude-code

# インストール確認
claude --version
```

Node.js が入っていない場合：
```bash
brew install node
```

---

## Step 2: リポジトリのクローン

```bash
git clone <contextAIのリポジトリURL>
cd contextAI

# サブモジュールも取得
git submodule update --init --recursive
```

---

## Step 3: Python 依存パッケージのインストール

```bash
# メインの依存パッケージ
pip install -r requirements.txt

# Mazrica クライアント用
pip install -r mixpanel/mazrica/requirements.txt
```

---

## Step 4: Mazrica API の設定

Mazrica APIキーが必要です。野田に聞いてください。

```bash
# .env ファイルを作成（mixpanel/mazrica/.env）
cp mixpanel/mazrica/.env.example mixpanel/mazrica/.env

# エディタで開いて API キーを設定
# MAZRICA_API_KEY=xxxxx
```

> .env ファイルは .gitignore に含まれており、リポジトリにはコミットされません。

---

## Step 5: MCP 連携の設定（Slack・Notion）

attack-prep は Claude Code の MCP（Model Context Protocol）経由で Slack と Notion を検索します。
claude.ai のアカウント連携で設定します。

### 5a. Claude Code を起動して初回認証

```bash
cd contextAI
claude
```

初回起動時に Anthropic アカウントへのログインが求められます。

### 5b. MCP サーバーの接続確認

Claude Code 内で以下を実行して、Slack・Notion が接続されているか確認：

```
/mcp
```

**Slack** と **Notion** が表示されていれば OK です。
表示されない場合は、claude.ai の Settings > Connected Apps から Slack / Notion を連携してください。

---

## Step 6: 動作確認

```bash
cd contextAI
claude
```

Claude Code のプロンプトで：

```
/attack-prep 東北 東京コンサルタンツ
```

以下が出力されれば成功：
- 企業概要（Mazrica）
- 連絡先一覧
- CiviLink / BIM/CIM 案件状況
- Slack での言及
- Notion 議事録
- 推奨アクション

---

## トラブルシューティング

### Mazrica API でエラーが出る
- `mixpanel/mazrica/.env` の API キーが正しいか確認
- `python3 -c "import requests; print('OK')"` で requests がインストールされているか確認

### Slack / Notion の検索結果が出ない
- `/mcp` で接続状態を確認
- claude.ai の Connected Apps で権限が付与されているか確認
- Slack は検索対象のチャンネルへの参加が必要（プライベートチャンネル含む）

### `/attack-prep` コマンドが見つからない
- `contextAI` ディレクトリ内で `claude` を起動しているか確認
- `.claude/commands/attack-prep.md` が存在するか確認

---

## 利用可能なスキル一覧

attack-prep 以外にも以下のスキルが使えます：

| コマンド | 用途 |
|---------|------|
| `/attack-prep {エリア} {会社名}` | アタック準備ブリーフィング |
| `/health-check` | 顧客ヘルスチェック |
| `/customer-prep` | 顧客MTG準備 |
| `/meeting-summary` | MTGサマリー・タスク抽出 |
| `/inquiry` | 顧客問い合わせ対応 |
| `/onboarding` | オンボーディング支援 |
| `/release-notify` | リリース案内作成 |

---

## 質問・サポート

セットアップで詰まったら野田（@nodatoshio）まで。
