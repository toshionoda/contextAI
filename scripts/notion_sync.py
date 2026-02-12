#!/usr/bin/env python3
"""
notion_sync.py - Notion AIミーティングノートを同期
環境変数: NOTION_API_TOKEN, NOTION_MEETING_DB_ID
"""

import os
import sys
import re
import json
import requests
from datetime import datetime, timedelta

NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN", "")
NOTION_MEETING_DB_ID = os.environ.get("NOTION_MEETING_DB_ID", "")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "context", "meetings")
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def sanitize_filename(name):
    """ファイル名に使えない文字を除去"""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_").replace("　", "_")
    return name[:100]


def get_meeting_pages(days_back=7):
    """ミーティングDBから最近のページ一覧を取得"""
    if not NOTION_MEETING_DB_ID:
        print("⚠️  NOTION_MEETING_DB_ID 未設定")
        return []

    url = f"https://api.notion.com/v1/databases/{NOTION_MEETING_DB_ID}/query"

    since = (datetime.now() - timedelta(days=days_back)).isoformat()
    payload = {
        "filter": {
            "property": "作成日時",
            "created_time": {"on_or_after": since},
        },
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        "page_size": 50,
    }

    # まずフィルタ付きで試行、失敗したらフィルタなしで取得
    resp = requests.post(url, headers=HEADERS, json=payload)
    if resp.status_code != 200:
        # フィルタなしでリトライ (DBスキーマが異なる場合)
        payload_simple = {
            "sorts": [{"timestamp": "created_time", "direction": "descending"}],
            "page_size": 50,
        }
        resp = requests.post(url, headers=HEADERS, json=payload_simple)
        if resp.status_code != 200:
            print(f"⚠️  Notion DB取得エラー: {resp.status_code} {resp.text[:200]}")
            return []

    data = resp.json()
    return data.get("results", [])


def get_page_blocks(page_id):
    """ページのブロック (本文) を取得"""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    all_blocks = []

    while url:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            break
        data = resp.json()
        all_blocks.extend(data.get("results", []))
        url = None
        if data.get("has_more"):
            cursor = data.get("next_cursor")
            url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100&start_cursor={cursor}"

    return all_blocks


def extract_rich_text(rich_text_array):
    """Notion rich_text 配列からプレーンテキストを抽出"""
    return "".join(rt.get("plain_text", "") for rt in rich_text_array)


def blocks_to_markdown(blocks, depth=0):
    """ブロック配列をMarkdownに変換"""
    lines = []
    for block in blocks:
        btype = block.get("type", "")
        prefix = "  " * depth

        if btype == "heading_1":
            text = extract_rich_text(block["heading_1"].get("rich_text", []))
            lines.append(f"\n## {text}\n")
        elif btype == "heading_2":
            text = extract_rich_text(block["heading_2"].get("rich_text", []))
            lines.append(f"\n### {text}\n")
        elif btype == "heading_3":
            text = extract_rich_text(block["heading_3"].get("rich_text", []))
            lines.append(f"\n#### {text}\n")
        elif btype == "paragraph":
            text = extract_rich_text(block["paragraph"].get("rich_text", []))
            if text.strip():
                lines.append(f"{prefix}{text}")
        elif btype == "bulleted_list_item":
            text = extract_rich_text(block["bulleted_list_item"].get("rich_text", []))
            lines.append(f"{prefix}- {text}")
        elif btype == "numbered_list_item":
            text = extract_rich_text(block["numbered_list_item"].get("rich_text", []))
            lines.append(f"{prefix}1. {text}")
        elif btype == "to_do":
            text = extract_rich_text(block["to_do"].get("rich_text", []))
            checked = block["to_do"].get("checked", False)
            mark = "x" if checked else " "
            lines.append(f"{prefix}- [{mark}] {text}")
        elif btype == "toggle":
            text = extract_rich_text(block["toggle"].get("rich_text", []))
            lines.append(f"{prefix}**{text}**")
        elif btype == "quote":
            text = extract_rich_text(block["quote"].get("rich_text", []))
            lines.append(f"{prefix}> {text}")
        elif btype == "divider":
            lines.append("---")
        elif btype == "callout":
            text = extract_rich_text(block["callout"].get("rich_text", []))
            lines.append(f"{prefix}> 💡 {text}")
        elif btype == "code":
            text = extract_rich_text(block["code"].get("rich_text", []))
            lang = block["code"].get("language", "")
            lines.append(f"{prefix}```{lang}\n{text}\n```")

        # 子ブロックがある場合は再帰
        if block.get("has_children") and btype not in ("child_page", "child_database"):
            child_blocks = get_page_blocks(block["id"])
            child_md = blocks_to_markdown(child_blocks, depth + 1)
            if child_md:
                lines.append(child_md)

    return "\n".join(lines)


def get_page_title(page):
    """ページのタイトルを取得"""
    props = page.get("properties", {})

    # タイトルプロパティを探す
    for key, val in props.items():
        if val.get("type") == "title":
            return extract_rich_text(val.get("title", []))

    # fallback: ページURL末尾からID取得
    return page.get("id", "untitled")


def sync_notion():
    if not NOTION_API_TOKEN:
        print("⚠️  NOTION_API_TOKEN が未設定です。")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    saved = 0

    # ミーティングDBが指定されていればDB経由
    if NOTION_MEETING_DB_ID:
        pages = get_meeting_pages(days_back=7)
        print(f"📋 Notion: {len(pages)}件のミーティングを検出")

        for page in pages:
            page_id = page["id"]
            title = get_page_title(page)
            if not title or title == page_id:
                title = "untitled"

            created = page.get("created_time", "")[:10]
            safe_title = sanitize_filename(title)
            filename = f"notion_{created}_{safe_title}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)

            # 既存ファイルがあればスキップ（更新チェック）
            last_edited = page.get("last_edited_time", "")
            if os.path.exists(filepath):
                # ファイル更新時刻と比較して変更なければスキップ
                existing_mtime = os.path.getmtime(filepath)
                try:
                    edited_ts = datetime.fromisoformat(last_edited.replace("Z", "+00:00")).timestamp()
                    if existing_mtime > edited_ts:
                        continue
                except (ValueError, OSError):
                    pass

            # ブロック取得 → Markdown変換
            blocks = get_page_blocks(page_id)
            content = blocks_to_markdown(blocks)

            if not content.strip():
                continue

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n")
                f.write(f"**日時**: {created}\n")
                f.write(f"**ソース**: Notion AIミーティングノート\n\n---\n\n")
                f.write(content)

            saved += 1
            print(f"  ✅ {filename}")

    print(f"✅ Notion同期完了: {saved}件保存")


if __name__ == "__main__":
    sync_notion()
