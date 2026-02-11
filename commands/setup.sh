#!/bin/bash
# setup.sh - CiviLink CS 初期セットアップ
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== CiviLink CS 初期セットアップ ==="
echo ""

# ディレクトリ構成の作成
echo "📁 ディレクトリ構成を確認中..."
dirs=(
    "context/slack"
    "context/calendar"
    "context/meetings"
    "context/daily"
    "customers/_template"
    "product/features"
    "product/release-notes"
    "product/known-issues"
    "product/competitive"
    "technical/docuworks"
    "technical/drawing-workflow"
    "technical/pc-bridge"
    "technical/standards"
    "skills"
    "commands"
    "scripts"
    "tasks/archive"
)

for dir in "${dirs[@]}"; do
    mkdir -p "$dir"
done
echo "✅ ディレクトリ構成 OK"

# .env ファイルの作成
if [ ! -f .env ]; then
    echo ""
    echo "📝 .env ファイルを作成中..."
    cat > .env << 'ENVEOF'
# CiviLink CS 環境変数

# Slack設定
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNELS=C01XXXXXXX,C02XXXXXXX

# Google Calendar設定
GOOGLE_CREDENTIALS_PATH=./credentials.json

# その他
TIMEZONE=Asia/Tokyo
ENVEOF
    echo "✅ .env を作成しました"
    echo "⚠️  .env にSlack/Calendar APIトークンを設定してください"
else
    echo "✅ .env 既に存在"
fi

# コマンドに実行権限を付与
echo ""
echo "🔧 実行権限を付与中..."
chmod +x commands/*.sh
echo "✅ 実行権限 OK"

# Python依存関係の確認
echo ""
echo "🐍 Python依存関係を確認中..."
python3 --version 2>/dev/null && echo "✅ Python3 OK" || echo "⚠️  Python3が見つかりません"

# 完了
echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. .env にSlack/Calendar APIトークンを設定"
echo "  2. ./commands/start-work.sh で始業開始"
echo ""
