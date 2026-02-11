#!/bin/bash
# end-work.sh - CiviLink CS 終業コマンド
# 日次サマリー → タスクアーカイブ → Git Push

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y-%m-%d_%H-%M)

echo "=== CiviLink CS 終業: $TODAY ==="
echo ""

# 完了タスクのアーカイブ
echo "📋 タスクアーカイブ..."
if [ -f tasks/todo.md ]; then
    # 完了済みタスク（[x]）を抽出してアーカイブ
    completed=$(grep "^\- \[x\]" tasks/todo.md 2>/dev/null || true)
    if [ -n "$completed" ]; then
        mkdir -p tasks/archive
        archive_file="tasks/archive/${TODAY}.md"
        echo "# 完了タスク: $TODAY" > "$archive_file"
        echo "" >> "$archive_file"
        echo "$completed" >> "$archive_file"
        echo "✅ ${archive_file} にアーカイブ"
    else
        echo "  完了タスクなし"
    fi
fi

# 日次サマリーの更新
echo ""
echo "📝 日次サマリー更新..."
summary_file="context/daily/${TODAY}_summary.md"
if [ -f "$summary_file" ]; then
    cat >> "$summary_file" << EOF

## 終業時メモ
- 終業時刻: $NOW
- 完了タスク数: $(grep -c "^\- \[x\]" tasks/todo.md 2>/dev/null || echo "0")
- 残タスク数: $(grep -c "^\- \[ \]" tasks/todo.md 2>/dev/null || echo "0")
EOF
    echo "✅ サマリー更新完了"
fi

# Git Push（リポジトリの場合）
echo ""
if [ -d .git ]; then
    echo "🔄 Git Push..."
    git add -A
    git commit -m "daily: ${TODAY} 終業" 2>/dev/null || echo "  コミットなし（変更なし）"
    git push 2>/dev/null && echo "✅ Push完了" || echo "⚠️  Push失敗（リモート未設定？）"
else
    echo "ℹ️  Gitリポジトリではないためスキップ"
fi

echo ""
echo "=== 終業完了: $NOW ==="
echo "お疲れさまでした！"
