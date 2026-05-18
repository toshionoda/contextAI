#!/usr/bin/env python3
"""
slack_summary.py - Claude Code CLI + Slack MCPで日次Slackサマリーを生成
外部依存: claude CLI のみ（slack_sdk, APIキー不要）
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "context", "slack_summary")
SUMMARY_DAYS = int(os.environ.get("SUMMARY_DAYS", "1"))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"{date_str}.md")

    after_date = (datetime.now() - timedelta(days=SUMMARY_DAYS)).strftime("%Y-%m-%d")

    prompt = f"""malme社のSlackから直近{SUMMARY_DAYS}日分（after:{after_date}）のメッセージを検索し、日次サマリーを生成してください。

## 検索対象チャンネル（重要度順）
以下のチャンネルを slack_search_public_and_private で検索してください：
1. in:proj-civilink after:{after_date}
2. in:dev-civilink after:{after_date}
3. in:マーケティング after:{after_date}
4. in:mail-civilink-cs after:{after_date}
5. in:shared_malme_am after:{after_date}
6. in:news after:{after_date}

各検索は limit:20, sort:timestamp, sort_dir:asc, include_context:false, response_format:concise でお願いします。
結果が20件ある場合はcursorで次ページも取得してください。

## まとめ方のルール
1. チャンネルごとではなく、**トピック/テーマごと**にまとめる
2. 各トピックで：誰が何を言ったか、決定事項、未解決事項、次のアクションを整理
3. 特にCiviLink関連（開発進捗、顧客対応、バグ報告）は詳しく
4. マーケティング・営業活動も重要
5. 人名は省略せず記載
6. 最後に「重要ポイント」テーブル（トピック/ステータス/次のアクション）を付ける
7. 出力はMarkdown形式。先頭に「# malme Slack サマリー: {date_str}」
8. **Markdownのみ出力。余計な前置き・後書き・説明は一切不要**"""

    print(f"📋 Slackサマリー生成開始 ({date_str})")
    print(f"   対象期間: 過去{SUMMARY_DAYS}日 (after:{after_date})")
    print(f"   方式: Claude Code CLI + Slack MCP")
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
                "mcp__claude_ai_Slack__slack_search_public_and_private,"
                "mcp__claude_ai_Slack__slack_search_public,"
                "mcp__claude_ai_Slack__slack_read_channel,"
                "mcp__claude_ai_Slack__slack_read_thread",
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
