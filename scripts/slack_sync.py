#!/usr/bin/env python3
"""
slack_sync.py - Slack直近3日分のメッセージを同期
環境変数: SLACK_BOT_TOKEN, SLACK_CHANNELS (カンマ区切り)
"""

import os
import json
import sys
from datetime import datetime, timedelta

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("slack_sdk未インストール: pip install slack_sdk")
    sys.exit(1)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNELS = os.environ.get("SLACK_CHANNELS", "").split(",")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context", "slack")

def sync_slack():
    if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN == "xoxb-your-slack-bot-token":
        print("SLACK_BOT_TOKEN が未設定です。.env に設定してください。")
        return

    client = WebClient(token=SLACK_BOT_TOKEN)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    oldest = (datetime.now() - timedelta(days=3)).timestamp()
    today = datetime.now().strftime("%Y-%m-%d")

    for channel_id in SLACK_CHANNELS:
        channel_id = channel_id.strip()
        if not channel_id:
            continue

        try:
            # チャンネル情報取得
            info = client.conversations_info(channel=channel_id)
            channel_name = info["channel"]["name"]

            # メッセージ取得
            result = client.conversations_history(
                channel=channel_id,
                oldest=str(oldest),
                limit=100
            )

            messages = result.get("messages", [])
            if not messages:
                continue

            # ファイル出力
            output_file = os.path.join(OUTPUT_DIR, f"{channel_name}_{today}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# #{channel_name} - 直近3日分 ({today})\n\n")
                for msg in reversed(messages):
                    ts = datetime.fromtimestamp(float(msg["ts"]))
                    user = msg.get("user", "unknown")
                    text = msg.get("text", "")
                    f.write(f"**{ts.strftime('%m/%d %H:%M')}** ({user}): {text}\n\n")

            print(f"✅ #{channel_name}: {len(messages)}件")

        except SlackApiError as e:
            print(f"⚠️ {channel_id}: {e.response['error']}")

if __name__ == "__main__":
    sync_slack()
