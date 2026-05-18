#!/usr/bin/env python3
"""
calendar_summary.py - Claude Code CLI + Google Calendar MCPで日次カレンダーサマリーを生成
外部依存: claude CLI のみ（APIキー不要）
取得内容: 前日のMTG振り返り + 本日の予定 + 今週の残り予定
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "context", "calendar")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"summary_{date_str}.md")

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    # 今週の金曜日を算出
    days_until_friday = (4 - datetime.now().weekday()) % 7
    if days_until_friday == 0 and datetime.now().weekday() == 4:
        days_until_friday = 0
    week_end = (datetime.now() + timedelta(days=max(days_until_friday, 1))).strftime("%Y-%m-%d")

    prompt = f"""Google Calendarから情報を取得し、日次カレンダーサマリーを生成してください。

## 取得手順（順番に実行）

### Step 1: 昨日のMTG振り返り
gcal_list_events で昨日（{yesterday}）のイベントを取得してください。
- timeMin: "{yesterday}T00:00:00"
- timeMax: "{yesterday}T23:59:59"
- timeZone: "Asia/Tokyo"
- condenseEventDetails: false（参加者情報も取得）

### Step 2: 本日の予定
gcal_list_events で今日（{today}）のイベントを取得してください。
- timeMin: "{today}T00:00:00"
- timeMax: "{today}T23:59:59"
- timeZone: "Asia/Tokyo"
- condenseEventDetails: false

### Step 3: 今週の残り予定
gcal_list_events で明日〜今週末（〜{week_end}）のイベントを取得してください。
- timeMin: "{today}T23:59:59"
- timeMax: "{week_end}T23:59:59"
- timeZone: "Asia/Tokyo"
- condenseEventDetails: true

## まとめ方のルール
1. **昨日のMTG振り返り** — 各MTGの名前、時間、参加者を一覧化。Google Meetリンクがあれば記録あり
2. **本日の予定** — 時系列で全イベントを表示。MTGは参加者・場所・Meet URLを含める
3. **今週の残り** — 日付ごとに主要予定を簡潔に表示
4. 社外MTG（顧客名が含まれるもの）は特に目立たせる
5. 出力はMarkdown形式。先頭に「# Calendar Summary: {date_str}」
6. **Markdownのみ出力。余計な前置き・後書き・説明は一切不要**"""

    print(f"📅 カレンダーサマリー生成開始 ({date_str})")
    print(f"   方式: Claude Code CLI + Google Calendar MCP")
    print()

    try:
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        result = subprocess.run(
            [
                "claude",
                "-p", prompt,
                "--output-format", "text",
                "--model", "sonnet",
                "--max-turns", "10",
                "--allowedTools",
                "mcp__claude_ai_Google_Calendar__list_events,"
                "mcp__claude_ai_Google_Calendar__get_event,"
                "mcp__claude_ai_Google_Calendar__list_calendars",
            ],
            capture_output=True,
            text=True,
            timeout=300,
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
        print("⚠ claude CLI タイムアウト（300秒）")
        sys.exit(1)

    # 古いサマリーのクリーンアップ（30日以上前）
    cleanup_cutoff = datetime.now() - timedelta(days=30)
    for fname in os.listdir(OUTPUT_DIR):
        if fname.startswith("summary_") and fname.endswith(".md"):
            try:
                fdate = datetime.strptime(fname.replace("summary_", "").replace(".md", ""), "%Y-%m-%d")
                if fdate < cleanup_cutoff:
                    os.remove(os.path.join(OUTPUT_DIR, fname))
                    print(f"🗑  古いサマリー削除: {fname}")
            except ValueError:
                pass


if __name__ == "__main__":
    main()
