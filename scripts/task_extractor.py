#!/usr/bin/env python3
"""
task_extractor.py - MTG議事録やSlackからタスクを自動抽出
"""

import os
import re
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
TASKS_FILE = os.path.join(PROJECT_ROOT, "tasks", "todo.md")


def extract_tasks_from_file(filepath):
    """ファイルからタスクパターンを抽出"""
    tasks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return tasks

    # パターン: TODO, アクション, タスク, 宿題 等
    patterns = [
        r"(?:TODO|タスク|アクション|宿題|対応)[：:]\s*(.+)",
        r"- \[ \]\s*(.+)",
        r"→\s*(.+?)(?:（|$)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            match = match.strip()
            if match and len(match) > 3:
                tasks.append(match)

    return tasks


def extract_from_meetings():
    """MTG議事録からタスク抽出"""
    meetings_dir = os.path.join(PROJECT_ROOT, "context", "meetings")
    tasks = []
    if os.path.isdir(meetings_dir):
        for fname in os.listdir(meetings_dir):
            if fname.endswith(".md"):
                filepath = os.path.join(meetings_dir, fname)
                file_tasks = extract_tasks_from_file(filepath)
                for t in file_tasks:
                    tasks.append({"source": f"meetings/{fname}", "task": t})
    return tasks


def extract_from_slack():
    """Slackログからタスク抽出"""
    slack_dir = os.path.join(PROJECT_ROOT, "context", "slack")
    tasks = []
    if os.path.isdir(slack_dir):
        for fname in os.listdir(slack_dir):
            if fname.endswith(".md"):
                filepath = os.path.join(slack_dir, fname)
                file_tasks = extract_tasks_from_file(filepath)
                for t in file_tasks:
                    tasks.append({"source": f"slack/{fname}", "task": t})
    return tasks


def main():
    all_tasks = extract_from_meetings() + extract_from_slack()

    if not all_tasks:
        print("新規タスクは見つかりませんでした")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== 抽出タスク ({today}) ===")
    for t in all_tasks:
        print(f"  [{t['source']}] {t['task']}")

    # tasks/todo.md に追記
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            existing = f.read()
    else:
        existing = ""

    new_tasks_section = f"\n## 🤖 自動抽出 ({today})\n"
    for t in all_tasks:
        task_line = f"- [ ] {t['task']}\n  - 出典: {t['source']}\n"
        if task_line not in existing:
            new_tasks_section += task_line

    if new_tasks_section.strip() != f"## 🤖 自動抽出 ({today})":
        with open(TASKS_FILE, "a", encoding="utf-8") as f:
            f.write(new_tasks_section)
        print(f"\n✅ {len(all_tasks)}件のタスクを tasks/todo.md に追記")
    else:
        print("全タスクが既に登録済みです")


if __name__ == "__main__":
    main()
