#!/bin/bash
# daily_morning.sh - 毎朝8時に自動実行される日次タスク
# crontab: 0 8 * * * /Users/nodatoshio/Documents/contextAI/scripts/daily_morning.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 環境変数読み込み
[ -f .env ] && export $(grep -v '^#' .env | xargs)

TODAY=$(date +%Y-%m-%d)
LOG_FILE="$PROJECT_ROOT/context/daily/morning_${TODAY}.log"
mkdir -p "$PROJECT_ROOT/context/daily"

exec > >(tee -a "$LOG_FILE") 2>&1

echo "=== Daily Morning Tasks: $TODAY $(date +%H:%M) ==="
echo ""

# 1. ニュース取得
echo "📰 ニュース取得中..."
python3 "$PROJECT_ROOT/scripts/news_sync.py" && echo "✅ ニュース取得完了" || echo "⚠️  ニュース取得スキップ"
echo ""

# 2. Slackサマリー生成（claude CLI + Slack MCP、トークン不要）
echo "📋 Slackサマリー生成中..."
python3 "$PROJECT_ROOT/scripts/slack_summary.py" && echo "✅ Slackサマリー完了" || echo "⚠️  Slackサマリースキップ"
echo ""

# 3. Notionサマリー生成（claude CLI + Notion MCP、トークン不要）
echo "📓 Notionサマリー生成中..."
python3 "$PROJECT_ROOT/scripts/notion_summary.py" && echo "✅ Notionサマリー完了" || echo "⚠️  Notionサマリースキップ"
echo ""

# 4. Calendarサマリー生成（claude CLI + Google Calendar MCP、credentials不要）
echo "📅 Calendarサマリー生成中..."
python3 "$PROJECT_ROOT/scripts/calendar_summary.py" && echo "✅ Calendarサマリー完了" || echo "⚠️  Calendarサマリースキップ"
echo ""

# 5. Slack生メッセージ同期
echo "💬 Slack同期中..."
if [ -n "$SLACK_BOT_TOKEN" ] && [ "$SLACK_BOT_TOKEN" != "xoxb-your-slack-bot-token" ]; then
    python3 "$PROJECT_ROOT/scripts/slack_sync.py" && echo "✅ Slack同期完了" || echo "⚠️  Slack同期スキップ"
else
    echo "⚠️  SLACK_BOT_TOKEN 未設定"
fi
echo ""

# 6. Calendar同期（Google API直接、credentials必要）
echo "📅 Calendar生データ同期中..."
if [ -f "${GOOGLE_CREDENTIALS_PATH:-$PROJECT_ROOT/credentials.json}" ]; then
    python3 "$PROJECT_ROOT/scripts/calendar_sync.py" && echo "✅ Calendar同期完了" || echo "⚠️  Calendar同期スキップ"
else
    echo "⚠️  Google credentials 未設定"
fi

# 7. 案件集約レポート生成（全ソースを横断して案件を自動集約）
echo ""
echo "📊 案件集約レポート生成中..."
python3 "$PROJECT_ROOT/scripts/case_aggregator.py" && echo "✅ 案件集約完了" || echo "⚠️  案件集約スキップ"

echo ""
echo "=== 完了: $(date +%H:%M) ==="
