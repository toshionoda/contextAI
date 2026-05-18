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

# 朝8時の自動取得結果を表示（daily_morning.sh で取得済み）
# 未取得の場合は始業時にキャッチアップで取得する（launchd が sleep 中で発火しなかった場合のフォールバック）
mkdir -p context/daily

NEED_DAILY_MORNING=0
[ ! -f "context/news/${TODAY}.md" ] && NEED_DAILY_MORNING=1
[ ! -f "context/slack_summary/${TODAY}.md" ] && NEED_DAILY_MORNING=1
[ ! -f "context/notion/${TODAY}.md" ] && NEED_DAILY_MORNING=1
[ ! -f "context/calendar/summary_${TODAY}.md" ] && NEED_DAILY_MORNING=1

if [ "$NEED_DAILY_MORNING" = "1" ]; then
    echo "=== 📡 本日分未取得 → daily_morning.sh をフォールバック実行（2〜5分）==="
    echo "    ログ: context/daily/morning_${TODAY}.log"
    bash scripts/daily_morning.sh > /dev/null 2>&1 || echo "    ⚠️  daily_morning.sh が一部失敗（ログ参照）"
    echo ""
fi

echo "=== 📰 本日のニュース ==="
if [ -f "context/news/${TODAY}.md" ]; then
    head -5 "context/news/${TODAY}.md"
    echo "  ...全文: context/news/${TODAY}.md"
else
    echo "  未取得（取得失敗。ログ: context/daily/morning_${TODAY}.log）"
fi
echo ""

echo "=== 📋 Slackサマリー ==="
if [ -f "context/slack_summary/${TODAY}.md" ]; then
    head -20 "context/slack_summary/${TODAY}.md"
    echo "  ...全文: context/slack_summary/${TODAY}.md"
else
    echo "  未取得（8時の自動実行待ち or scripts/daily_morning.sh を手動実行）"
fi

echo ""

echo "=== 📓 Notionサマリー ==="
if [ -f "context/notion/${TODAY}.md" ]; then
    head -20 "context/notion/${TODAY}.md"
    echo "  ...全文: context/notion/${TODAY}.md"
else
    echo "  未取得（8時の自動実行待ち or scripts/daily_morning.sh を手動実行）"
fi

echo ""

echo "=== 📅 Calendarサマリー ==="
if [ -f "context/calendar/summary_${TODAY}.md" ]; then
    head -30 "context/calendar/summary_${TODAY}.md"
    echo "  ...全文: context/calendar/summary_${TODAY}.md"
else
    echo "  未取得（8時の自動実行待ち or scripts/daily_morning.sh を手動実行）"
fi

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

# 案件集約レポート
echo "=== 📊 案件集約 ==="
CASES_FILE="context/cases/${TODAY}.md"
if [ -f "$CASES_FILE" ]; then
    head -50 "$CASES_FILE"
    echo "  ...全文: $CASES_FILE"
else
    echo "  未生成（scripts/case_aggregator.py を実行、または8時の自動実行待ち）"
fi

echo ""

# CRM Inbox処理
echo "=== 📬 CRM Inbox ==="
if python3 scripts/crm_inbox_processor.py 2>&1; then
    :
else
    echo "  CRM Inbox処理をスキップ（環境変数未設定 or チャンネル未作成）"
fi

echo ""

# タスク表示
echo "=== 📋 タスク ==="
cat tasks/todo.md 2>/dev/null || echo "タスクなし"

echo ""
echo "=== 始業完了 ==="
echo '💡 「始業チェックスキルを実行して」で詳細分析'
echo '💡 「JRCのMTG準備して」で顧客MTG準備'
