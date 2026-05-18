"""
顧客管理スプレッドシート → Notion「組織別利用状況」DB 同期スクリプト

Google Sheetsの「Civilink_ユーザー」シートから組織名・登録ユーザー数・契約者情報を取得し、
Notion DBの該当レコードを更新する。

毎日の自動実行を想定。

必要な環境変数:
  - CS_PANEL_GOOGLE_CREDENTIALS_JSON: Google Sheets API認証情報
  - NOTION_API_KEY: Notion Internal Integration Token
"""
from __future__ import annotations

import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime

import requests

# mixpanelプロジェクトのパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mixpanel"))
from mazrica.google_sheets_client import GoogleSheetsClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# --- 設定 ---
CUSTOMER_SHEET_ID = "13omnSua9aFd937r6ZbfArch7uL_1gLJ3QF4hOozDI0Y"
USER_SHEET_NAME = "Civilink_ユーザー"
NOTION_DB_ID = "9ac9caa0-cd13-440d-838e-09c0e4476106"
EXCLUDED_DOMAINS = {"malme.co.jp", "malme.app", "gmail.com", "example.com"}


def get_notion_headers() -> dict:
    token = os.environ.get("NOTION_API_KEY", "")
    if not token:
        raise ValueError("NOTION_API_KEY が設定されていません")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }


def fetch_sheet_data(csv_path: str | None = None) -> list[list[str]]:
    """Google SheetsまたはローカルCSVから顧客ユーザーデータを取得"""
    if csv_path and os.path.exists(csv_path):
        import csv
        with open(csv_path, encoding="utf-8") as f:
            data = list(csv.reader(f))
        logger.info(f"CSV から {len(data)} 行取得: {csv_path}")
        return data

    creds_json = os.environ.get("CS_PANEL_GOOGLE_CREDENTIALS_JSON", "")
    if not creds_json:
        raise ValueError(
            "CS_PANEL_GOOGLE_CREDENTIALS_JSON が設定されていません。"
            " --csv オプションでローカルCSVを指定してください。"
        )

    client = GoogleSheetsClient(
        credentials_json=creds_json,
        spreadsheet_id=CUSTOMER_SHEET_ID,
    )
    data = client.read_data(USER_SHEET_NAME)
    logger.info(f"Google Sheets から {len(data)} 行取得")
    return data


def aggregate_orgs(rows: list[list[str]]) -> dict[str, dict]:
    """ドメイン別に組織情報を集約"""
    if not rows:
        return {}

    header = rows[0]
    col = {name: i for i, name in enumerate(header)}

    orgs: dict[str, dict] = defaultdict(lambda: {
        "org_name": "",
        "users": set(),
        "owners": {},  # email -> name
    })

    for row in rows[1:]:
        def get(name: str) -> str:
            idx = col.get(name)
            if idx is None or idx >= len(row):
                return ""
            return str(row[idx]).strip()

        org_name = get("組織名")
        if not org_name or org_name == "株式会社Malme":
            continue

        user_email = get("ユーザーメールアドレス")
        if not user_email or "@" not in user_email:
            continue

        domain = user_email.split("@")[1]
        if domain in EXCLUDED_DOMAINS:
            continue

        entry = orgs[domain]
        if not entry["org_name"]:
            entry["org_name"] = org_name
        entry["users"].add(user_email)

        owner_email = get("組織メールアドレス")
        owner_name = get("契約者名")
        if owner_email and owner_email not in entry["owners"]:
            entry["owners"][owner_email] = owner_name

    logger.info(f"{len(orgs)} ドメインに集約")
    return dict(orgs)


def fetch_notion_pages() -> list[dict]:
    """Notion DBの全ページを取得"""
    headers = get_notion_headers()
    url = f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query"
    pages = []
    payload: dict = {"page_size": 100}

    while True:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]

    logger.info(f"Notion DB から {len(pages)} ページ取得")
    return pages


def get_domain_from_page(page: dict) -> str:
    """Notionページからドメインプロパティを取得"""
    prop = page.get("properties", {}).get("ドメイン", {})
    rich_texts = prop.get("rich_text", [])
    if rich_texts:
        return rich_texts[0].get("plain_text", "").strip()
    return ""


def update_notion_page(page_id: str, org_data: dict) -> bool:
    """Notionページを更新"""
    headers = get_notion_headers()
    url = f"https://api.notion.com/v1/pages/{page_id}"

    owner_count = len(org_data["owners"])
    owner_list = ", ".join(
        f"{name}({email})" for email, name in org_data["owners"].items()
    )
    user_count = len(org_data["users"])
    today = datetime.now().strftime("%Y-%m-%d")

    properties: dict = {
        "組織名": {"title": [{"text": {"content": org_data["org_name"]}}]},
        "登録ユーザー数": {"number": user_count},
        "契約者数": {"number": owner_count},
        "契約者一覧": {"rich_text": [{"text": {"content": owner_list[:2000]}}]},
        "データ更新日": {"date": {"start": today}},
    }

    resp = requests.patch(url, headers=headers, json={"properties": properties}, timeout=30)
    if resp.status_code == 200:
        return True
    else:
        logger.error(f"更新失敗 {page_id}: {resp.status_code} {resp.text[:200]}")
        return False


def create_notion_page(org_data: dict, domain: str) -> bool:
    """新規組織をNotionに追加"""
    headers = get_notion_headers()
    url = "https://api.notion.com/v1/pages"

    owner_count = len(org_data["owners"])
    owner_list = ", ".join(
        f"{name}({email})" for email, name in org_data["owners"].items()
    )
    user_count = len(org_data["users"])
    today = datetime.now().strftime("%Y-%m-%d")

    properties: dict = {
        "組織名": {"title": [{"text": {"content": org_data["org_name"]}}]},
        "ドメイン": {"rich_text": [{"text": {"content": domain}}]},
        "登録ユーザー数": {"number": user_count},
        "契約者数": {"number": owner_count},
        "契約者一覧": {"rich_text": [{"text": {"content": owner_list[:2000]}}]},
        "契約ステータス": {"select": {"name": "トライアル"}},
        "有償化フェーズ": {"select": {"name": "未着手"}},
        "ヘルススコア": {"select": {"name": "未評価"}},
        "データ更新日": {"date": {"start": today}},
    }

    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    if resp.status_code == 200:
        return True
    else:
        logger.error(f"作成失敗 {domain}: {resp.status_code} {resp.text[:200]}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="顧客管理シート → Notion DB 同期")
    parser.add_argument("--dry-run", action="store_true", help="更新を実行しない")
    parser.add_argument("--add-new", action="store_true", help="Notion DBにない組織も新規追加する")
    parser.add_argument("--min-users", type=int, default=3, help="新規追加時の最小ユーザー数（デフォルト: 3）")
    parser.add_argument("--csv", type=str, default=None, help="ローカルCSVファイルパス（Google Sheets未設定時のフォールバック）")
    args = parser.parse_args()

    logger.info("=== 顧客管理シート → Notion DB 同期開始 ===")

    # 1. データ取得（Google Sheets or ローカルCSV）
    rows = fetch_sheet_data(csv_path=args.csv)
    orgs = aggregate_orgs(rows)

    # 2. Notion DBの既存ページ取得
    pages = fetch_notion_pages()
    domain_to_page = {}
    for page in pages:
        domain = get_domain_from_page(page)
        if domain:
            domain_to_page[domain] = page["id"]

    # 3. 既存ページを更新
    updated = 0
    for domain, page_id in domain_to_page.items():
        if domain in orgs:
            org_data = orgs[domain]
            if args.dry_run:
                logger.info(f"[dry-run] 更新: {org_data['org_name']} ({domain}) "
                           f"ユーザー={len(org_data['users'])} 契約者={len(org_data['owners'])}")
            else:
                if update_notion_page(page_id, org_data):
                    logger.info(f"更新: {org_data['org_name']} ({domain})")
                    updated += 1
        else:
            logger.warning(f"マッチなし: {domain}")

    # 4. 新規組織を追加（オプション）
    created = 0
    if args.add_new:
        existing_domains = set(domain_to_page.keys())
        for domain, org_data in orgs.items():
            if domain not in existing_domains and len(org_data["users"]) >= args.min_users:
                if args.dry_run:
                    logger.info(f"[dry-run] 新規追加: {org_data['org_name']} ({domain}) "
                               f"ユーザー={len(org_data['users'])} 契約者={len(org_data['owners'])}")
                else:
                    if create_notion_page(org_data, domain):
                        logger.info(f"新規追加: {org_data['org_name']} ({domain})")
                        created += 1

    logger.info(f"=== 完了: 更新={updated}, 新規={created} ===")


if __name__ == "__main__":
    main()
