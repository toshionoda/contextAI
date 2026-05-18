#!/usr/bin/env python3
"""
case_aggregator.py - 全ソースから案件情報を自動集約
Slack/Calendar/Notion/MTG議事録/顧客ディレクトリを横断し、
アクティブな案件の最新状況を1つのファイルにまとめる。

daily_morning.sh の最終ステップとして実行される。
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "context" / "cases"
LOOKBACK_DAYS = int(os.environ.get("CASE_LOOKBACK_DAYS", "3"))


def collect_recent_files(directory: Path, days: int, suffix: str = ".md") -> list[dict]:
    """指定ディレクトリから直近N日のファイルを収集"""
    if not directory.is_dir():
        return []

    cutoff = datetime.now() - timedelta(days=days)
    files = []
    for f in sorted(directory.iterdir()):
        if not f.name.endswith(suffix):
            continue
        # ファイル名から日付を推測、もしくはmtimeで判定
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime >= cutoff:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if content.strip():
                files.append({
                    "path": str(f.relative_to(PROJECT_ROOT)),
                    "content": content[:3000],  # 先頭3000文字に制限
                })
    return files


def collect_customer_readmes() -> list[dict]:
    """顧客ディレクトリのREADMEを収集"""
    customers_dir = PROJECT_ROOT / "customers"
    files = []
    if not customers_dir.is_dir():
        return files
    for d in sorted(customers_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        readme = d / "README.md"
        if readme.exists():
            content = readme.read_text(encoding="utf-8", errors="ignore")
            files.append({
                "path": str(readme.relative_to(PROJECT_ROOT)),
                "content": content[:2000],
            })
    return files


def build_context() -> str:
    """集約対象のコンテキストを構築"""
    sections = []

    # 1. Slackサマリー
    slack_files = collect_recent_files(PROJECT_ROOT / "context" / "slack_summary", LOOKBACK_DAYS)
    if slack_files:
        sections.append("## Slackサマリー（直近{}日）".format(LOOKBACK_DAYS))
        for f in slack_files:
            sections.append(f"### {f['path']}\n{f['content']}")

    # 2. Notionサマリー
    notion_files = collect_recent_files(PROJECT_ROOT / "context" / "notion", LOOKBACK_DAYS)
    if notion_files:
        sections.append("## Notionサマリー")
        for f in notion_files:
            sections.append(f"### {f['path']}\n{f['content']}")

    # 3. Calendarサマリー
    cal_files = collect_recent_files(PROJECT_ROOT / "context" / "calendar", LOOKBACK_DAYS)
    if cal_files:
        sections.append("## Calendarサマリー")
        for f in cal_files:
            sections.append(f"### {f['path']}\n{f['content']}")

    # 4. MTG議事録
    mtg_files = collect_recent_files(PROJECT_ROOT / "context" / "meetings", LOOKBACK_DAYS * 3)
    if mtg_files:
        sections.append("## MTG議事録（直近{}日）".format(LOOKBACK_DAYS * 3))
        for f in mtg_files:
            sections.append(f"### {f['path']}\n{f['content']}")

    # 5. 顧客README
    customer_files = collect_customer_readmes()
    if customer_files:
        sections.append("## 顧客ステータス")
        for f in customer_files:
            sections.append(f"### {f['path']}\n{f['content']}")

    # 6. 既存タスク
    todo_path = PROJECT_ROOT / "tasks" / "todo.md"
    if todo_path.exists():
        content = todo_path.read_text(encoding="utf-8", errors="ignore")
        sections.append(f"## 現在のタスク\n{content[:3000]}")

    return "\n\n".join(sections)


def generate_aggregation(context: str) -> str | None:
    """Claude CLIで案件集約レポートを生成"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 前回の集約があれば差分検知に使う
    prev_report = ""
    prev_files = sorted(OUTPUT_DIR.glob("*.md"), reverse=True)
    if prev_files:
        prev_report = prev_files[0].read_text(encoding="utf-8", errors="ignore")[:2000]

    prompt = f"""以下は直近のSlack、Calendar、Notion、MTG議事録、顧客情報、タスクリストです。
これらから**現在アクティブな全案件**を抽出し、案件集約レポートを生成してください。

# ルール
1. 案件ごとに以下をまとめる：
   - 案件名（顧客名 + 内容）
   - ステータス（🔴緊急 / 🟡進行中 / 🟢順調 / 🔵待ち / ⚪未着手）
   - 最新の動き（直近の出来事を1-3行で）
   - 次のアクション（担当者 + 期限があれば記載）
   - 出典（情報源ファイル名）
2. 案件はステータス順（🔴→🟡→🟢→🔵→⚪）でソート
3. 最後に「今日注目すべき案件」をサマリーテーブルで出す
4. 出力はMarkdown形式。先頭に「# 案件集約レポート: {today}」
5. **Markdownのみ出力。余計な前置き・後書き不要**

{f"# 前回のレポート（差分検知用）{chr(10)}{prev_report}" if prev_report else ""}

# 入力データ
{context}"""

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            [
                "claude",
                "-p", prompt,
                "--output-format", "text",
                "--model", "haiku",
                "--max-turns", "3",
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(PROJECT_ROOT),
            env=env,
        )

        if result.returncode != 0:
            print(f"❌ claude CLI エラー (code {result.returncode})")
            if result.stderr:
                print(f"   stderr:\n{result.stderr}")
            if result.stdout:
                print(f"   stdout:\n{result.stdout}")
            return None

        output = result.stdout.strip()
        return output if output else None

    except FileNotFoundError:
        print("❌ claude CLI が見つかりません")
        return None
    except subprocess.TimeoutExpired:
        print("⚠ claude CLI タイムアウト（300秒）")
        return None


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{today}.md"

    print(f"📊 案件集約開始 ({today})")
    print(f"   対象期間: 直近{LOOKBACK_DAYS}日")
    print(f"   方式: Claude Code CLI")
    print()

    # コンテキスト収集
    print("   📂 コンテキスト収集中...")
    context = build_context()
    if not context.strip():
        print("⚠ 集約対象のデータがありません")
        return

    context_size = len(context)
    print(f"   📊 収集データ: {context_size:,}文字")

    # Claude CLIで集約
    print("   🤖 案件集約レポート生成中...")
    report = generate_aggregation(context)

    if not report:
        print("❌ レポート生成失敗")
        return

    # 保存
    report_with_meta = f"""{report}

---
*生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 対象期間: 直近{LOOKBACK_DAYS}日 | データ量: {context_size:,}文字*
"""
    output_path.write_text(report_with_meta, encoding="utf-8")
    print(f"💾 保存: {output_path}")

    # 古いレポートのクリーンアップ（14日以上前）
    cleanup_cutoff = datetime.now() - timedelta(days=14)
    for f in OUTPUT_DIR.glob("*.md"):
        try:
            fdate = datetime.strptime(f.stem, "%Y-%m-%d")
            if fdate < cleanup_cutoff:
                f.unlink()
                print(f"🗑  古いレポート削除: {f.name}")
        except ValueError:
            pass

    print()
    print("✅ 案件集約完了")


if __name__ == "__main__":
    main()
