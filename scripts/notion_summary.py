#!/usr/bin/env python3
"""
notion_summary.py - Claude Code CLI + Notion MCPで日次Notionサマリーを生成
外部依存: claude CLI のみ（APIキー不要）
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "context", "notion")
SUMMARY_DAYS = int(os.environ.get("SUMMARY_DAYS", "1"))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"{date_str}.md")

    after_date = (datetime.now() - timedelta(days=SUMMARY_DAYS)).strftime("%Y-%m-%d")

    prompt = f"""malme社のNotionワークスペースから直近{SUMMARY_DAYS}日分の情報を取得し、日次サマリーを生成してください。

## 取得手順（順番に実行）

### Step 1: MTG議事録
notion-query-meeting-notes を使って直近の会議ノートを取得してください。

### Step 2: 最近更新されたページの検索
notion-search で以下のキーワードを検索してください（各 limit:10）：
- "CiviLink"
- "タスク"
- "議事録"
- "スプリント"
結果から {after_date} 以降に更新されたページを抽出してください。

### Step 3: 重要ページの詳細取得
Step 1, 2で見つかった重要なページは notion-fetch で詳細を取得してください。
特にCiviLink関連、プロダクト開発、顧客対応に関するものを優先。

## まとめ方のルール
1. **MTG議事録** — 会議名、日時、参加者、決定事項、アクションアイテムを整理
2. **タスク/進捗** — データベースから取得したタスクのステータスを一覧化
3. **最近の更新** — 重要な更新があったページの概要
4. 人名は省略せず記載
5. 最後に「アクションアイテム」テーブル（担当者/内容/期限）を付ける
6. 出力はMarkdown形式。先頭に「# Notion Daily Summary: {date_str}」
7. **Markdownのみ出力。余計な前置き・後書き・説明は一切不要**"""

    print(f"📓 Notionサマリー生成開始 ({date_str})")
    print(f"   対象期間: 過去{SUMMARY_DAYS}日 (after:{after_date})")
    print(f"   方式: Claude Code CLI + Notion MCP")
    print()

    try:
        # CLAUDECODE環境変数を外してネスト制限を回避
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        result = subprocess.run(
            [
                "claude",
                "-p", prompt,
                "--output-format", "text",
                "--model", "sonnet",
                "--max-turns", "15",
                "--allowedTools",
                "mcp__claude_ai_Notion__notion-search,"
                "mcp__claude_ai_Notion__notion-fetch,"
                "mcp__claude_ai_Notion__notion-query-meeting-notes,"
                "mcp__claude_ai_Notion__notion-query-data-sources,"
                "mcp__claude_ai_Notion__notion-get-comments",
            ],
            capture_output=True,
            text=True,
            timeout=600,
            cwd=PROJECT_ROOT,
            env=env,
        )

        if result.returncode != 0:
            print(f"❌ claude CLI エラー (code {result.returncode})")
            if result.stderr:
                print(f"   stderr:\n{result.stderr}")
            if result.stdout:
                print(f"   stdout:\n{result.stdout}")
            sys.exit(1)

        summary = result.stdout.strip()
        if not summary:
            print("❌ 出力が空でした")
            sys.exit(1)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(summary)

        print(f"💾 保存: {output_path}")

    except FileNotFoundError:
        print("❌ claude CLI が見つかりません")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print("⚠ claude CLI タイムアウト（600秒）")
        sys.exit(1)

    # 古いサマリーのクリーンアップ（30日以上前）
    cleanup_cutoff = datetime.now() - timedelta(days=30)
    for fname in os.listdir(OUTPUT_DIR):
        if fname.endswith(".md"):
            try:
                fdate = datetime.strptime(fname.replace(".md", ""), "%Y-%m-%d")
                if fdate < cleanup_cutoff:
                    os.remove(os.path.join(OUTPUT_DIR, fname))
                    print(f"🗑  古いサマリー削除: {fname}")
            except ValueError:
                pass


if __name__ == "__main__":
    main()
