#!/usr/bin/env python3
"""
slack_sync.py - Slackのメッセージを同期
環境変数:
  SLACK_BOT_TOKEN  - 必須
  SLACK_CHANNELS   - "all" で全チャンネル / カンマ区切りでチャンネルID指定 / 空欄で全チャンネル
  SLACK_DAYS       - 取得日数（省略時 3）。照査AIトライアル等を多く探す場合は 30 を推奨
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
SLACK_CHANNELS_ENV = os.environ.get("SLACK_CHANNELS", "all").strip()
SLACK_DAYS = int(os.environ.get("SLACK_DAYS", "3"))
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context", "slack")


def get_all_channels(client):
    """組織全体のチャンネルを取得し、未参加チャンネルには自動でjoinする"""
    channels = []
    cursor = None

    while True:
        kwargs = {
            "types": "public_channel,private_channel",
            "exclude_archived": True,
            "limit": 200,
        }
        if cursor:
            kwargs["cursor"] = cursor

        result = client.conversations_list(**kwargs)
        for ch in result.get("channels", []):
            channels.append({
                "id": ch["id"],
                "name": ch["name"],
                "is_member": ch.get("is_member", False),
            })

        cursor = result.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break

    print(f"📡 組織全体のチャンネル: {len(channels)}件")

    # 未参加のpublicチャンネルに自動join（privateはjoin不可なのでスキップ）
    joined = 0
    for ch in channels:
        if not ch["is_member"]:
            try:
                client.conversations_join(channel=ch["id"])
                ch["is_member"] = True
                joined += 1
            except SlackApiError:
                pass  # private channel など参加不可の場合はスキップ

    if joined:
        print(f"✅ {joined}チャンネルに自動参加しました")

    # 参加済み（または参加成功）チャンネルのみ返す
    accessible = [ch for ch in channels if ch["is_member"]]
    print(f"📨 メッセージ取得対象: {len(accessible)}チャンネル")
    return accessible


def resolve_channels(client):
    """SLACK_CHANNELS設定に基づいてチャンネルリストを決定"""
    if not SLACK_CHANNELS_ENV or SLACK_CHANNELS_ENV.lower() == "all":
        return get_all_channels(client)

    # カンマ区切りのチャンネルID指定
    channel_list = []
    for cid in SLACK_CHANNELS_ENV.split(","):
        cid = cid.strip()
        if not cid:
            continue
        try:
            info = client.conversations_info(channel=cid)
            channel_list.append({
                "id": cid,
                "name": info["channel"]["name"],
            })
        except SlackApiError as e:
            print(f"⚠️ チャンネル {cid} の情報取得失敗: {e.response['error']}")
    return channel_list


def sync_slack():
    if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN == "xoxb-your-slack-bot-token":
        print("SLACK_BOT_TOKEN が未設定です。.env に設定してください。")
        return

    client = WebClient(token=SLACK_BOT_TOKEN)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    oldest = (datetime.now() - timedelta(days=SLACK_DAYS)).timestamp()
    today = datetime.now().strftime("%Y-%m-%d")

    channels = resolve_channels(client)
    synced = 0

    for ch in channels:
        channel_id = ch["id"]
        channel_name = ch["name"]

        try:
            messages = []
            cursor = None
            while True:
                kwargs = {
                    "channel": channel_id,
                    "oldest": str(oldest),
                    "limit": 200,
                }
                if cursor:
                    kwargs["cursor"] = cursor
                result = client.conversations_history(**kwargs)
                batch = result.get("messages", [])
                messages.extend(batch)
                cursor = result.get("response_metadata", {}).get("next_cursor", "")
                if not cursor or len(batch) < 200:
                    break

            if not messages:
                continue

            messages.sort(key=lambda m: float(m["ts"]))
            output_file = os.path.join(OUTPUT_DIR, f"{channel_name}_{today}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# #{channel_name} - 直近{SLACK_DAYS}日分 ({today})\n\n")
                for msg in messages:
                    ts = datetime.fromtimestamp(float(msg["ts"]))
                    user = msg.get("user", "unknown")
                    text = msg.get("text", "")
                    f.write(f"**{ts.strftime('%m/%d %H:%M')}** ({user}): {text}\n\n")

            print(f"✅ #{channel_name}: {len(messages)}件")
            synced += 1

        except SlackApiError as e:
            print(f"⚠️ #{channel_name} ({channel_id}): {e.response['error']}")

    print(f"\n📊 同期完了: {synced}/{len(channels)} チャンネル（直近{SLACK_DAYS}日分）")


if __name__ == "__main__":
    sync_slack()
