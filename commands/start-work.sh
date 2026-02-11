#!/bin/bash
# start-work.sh - CiviLink CS 始業コマンド
# Slack/Calendar同期 → 顧客アラート確認 → タスク表示

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

[ -f .env ] && export $(grep -v '^#' .env | xargs)

TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H-%M)

echo "=== CiviLink CS 始業: $TODAY ==="
echo ""

# Git Pull
[ -d .git ] && git pull --quiet 2>/dev/null || true

# Slack同期
echo "💬 Slack同期中..."
if [ -n "$SLACK_BOT_TOKEN" ] && [ "$SLACK_BOT_TOKEN" != "xoxb-your-slack-bot-token" ]; then
    python3 scripts/slack_sync.py 2>/dev/null && echo "✅ Slack同期完了" || echo "⚠️  スキップ"
else
    echo "⚠️  SLACK_BOT_TOKEN 未設定"
fi

# Calendar同期
echo "📅 Calendar同期中..."
[ -f "${GOOGLE_CREDENTIALS_PATH:-./credentials.json}" ] && \
    python3 scripts/calendar_sync.py 2>/dev/null && echo "✅ Calendar同期完了" || echo "⚠️  スキップ"

echo ""

# 顧客アラート
echo "=== 🚨 顧客アラート ==="
for customer_dir in customers/*/; do
    [ -d "$customer_dir" ] || continue
    customer_name=$(basename "$customer_dir")
    [ "$customer_name" = "_template" ] && continue
    
    readme="$customer_dir/README.md"
    if [ -f "$readme" ]; then
        # ヘルススコアを表示
        health=$(grep -o "🔴\|🟡\|🟢\|🔵\|⚪" "$readme" | tail -1)
        echo "  $health $customer_name"
        
        # 🔴の場合は未解決課題を表示
        if [ "$health" = "🔴" ] && [ -f "$customer_dir/issues.md" ]; then
            grep "^\- \[ \]" "$customer_dir/issues.md" 2>/dev/null | head -3 | while read line; do
                echo "     $line"
            done
        fi
    fi
done

echo ""

# MTG確認
echo "=== 📅 本日のMTG ==="
if [ -f "context/calendar/schedule_${TODAY}.md" ]; then
    grep -i "mtg\|meeting\|打合\|ミーティング" "context/calendar/schedule_${TODAY}.md" 2>/dev/null || echo "  MTGなし"
else
    echo "  Calendar未同期"
fi

echo ""

# 日次サマリー
mkdir -p context/daily
cat > "context/daily/${TODAY}_summary.md" << EOF
# CiviLink CS 日次サマリー: $TODAY
生成: $NOW

## 顧客ステータス
$(for d in customers/*/; do
    [ -d "$d" ] || continue
    n=$(basename "$d")
    [ "$n" = "_template" ] && continue
    r="$d/README.md"
    [ -f "$r" ] && echo "- $(grep -o '🔴\|🟡\|🟢\|🔵\|⚪' "$r" | tail -1) $n" || echo "- ❓ $n"
done)

## 本日のMTG
$(cat "context/calendar/schedule_${TODAY}.md" 2>/dev/null || echo "未同期")
EOF

# タスク表示
echo "=== 📋 タスク ==="
cat tasks/todo.md 2>/dev/null || echo "タスクなし"

echo ""
echo "=== 始業完了 ==="
echo '💡 「始業チェックスキルを実行して」で詳細分析'
echo '💡 「JRCのMTG準備して」で顧客MTG準備'
