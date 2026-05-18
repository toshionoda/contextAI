#!/usr/bin/env python3
"""
crm_inbox_processor.py - Slack #crm-inbox の投稿を自動で構造化しMazricaに登録

Slack #crm-inbox チャンネルに投げられた名刺写真・音声メモ・テキストメモを
自動で構造化し、Mazrica（取引先・コンタクト・案件）に登録する。

処理フロー:
  1. Slack #crm-inbox から未処理メッセージを取得
  2. メッセージを分類（名刺画像 / 音声メモ / テキスト）
  3. Gemini Vision/Audio または Claude で構造化抽出
  4. Mazrica に登録（既存チェック → 新規 or 更新）
  5. Slack スレッドに確認返信

環境変数:
  SLACK_BOT_TOKEN    - Slack Bot Token（必須）
  GOOGLE_API_KEY     - Gemini API キー（名刺OCR・音声文字起こし用）
  ANTHROPIC_API_KEY  - Claude API キー（構造化抽出用）
  MAZRICA_API_KEY    - Mazrica API キー（必須）
  MAZRICA_DEAL_TYPE_ID - デフォルトの案件タイプID（任意）
  CRM_INBOX_CHANNEL  - Slack チャンネル名（デフォルト: crm-inbox）

使い方:
  # 基本（未処理メッセージを一括処理）
  python3 scripts/crm_inbox_processor.py

  # ドライラン（Mazrica書き込み・Slack返信なし）
  python3 scripts/crm_inbox_processor.py --dry-run

  # 直近N日分を再処理
  python3 scripts/crm_inbox_processor.py --days 7
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

# .env 読み込み
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# --- 依存ライブラリのインポート ---

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    print("slack_sdk未インストール: pip install slack_sdk", file=sys.stderr)
    sys.exit(1)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("google-genai未インストール: pip install google-genai", file=sys.stderr)
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("anthropic未インストール: pip install anthropic", file=sys.stderr)
    sys.exit(1)

# Mazrica クライアント（mazrica-civilink サブモジュール）
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mazrica-civilink"))
from mazrica.mazrica_client import MazricaClient, MazricaAPIError

from crm_prompts import (
    BUSINESS_CARD_PROMPT,
    TEXT_NOTE_PROMPT,
    VOICE_MEMO_PROMPT,
    format_confirmation,
)

# --- 設定 ---

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MAZRICA_API_KEY = os.environ.get("MAZRICA_API_KEY", "")
MAZRICA_DEAL_TYPE_ID = os.environ.get("MAZRICA_DEAL_TYPE_ID", "")
MAZRICA_APP_URL = os.environ.get("MAZRICA_APP_URL", "https://senses.mazrica.com/r")
CRM_INBOX_CHANNEL = os.environ.get("CRM_INBOX_CHANNEL", "crm-inbox")

STATE_DIR = Path(__file__).resolve().parent.parent / "context" / "crm_inbox"
STATE_FILE = STATE_DIR / "last_processed.json"


# ============================================================
# ユーティリティ
# ============================================================

def load_state() -> dict:
    """最後に処理したメッセージのタイムスタンプを読み込む"""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_ts": "0"}


def save_state(state: dict):
    """処理済みタイムスタンプを保存"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def extract_json_from_text(text: str) -> dict | list:
    """LLM応答からJSONを抽出"""
    # ```json ... ``` ブロックを探す
    # ```json ... ``` ブロックを探す
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # ブロックなし → JSONオブジェクト/配列を探す
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"JSONを抽出できません: {text[:200]}...")


# ============================================================
# Slack: メッセージ取得
# ============================================================

def find_channel_id(client: WebClient, channel_name: str) -> str | None:
    """チャンネル名からIDを取得"""
    cursor = None
    while True:
        kwargs = {"types": "public_channel,private_channel", "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        result = client.conversations_list(**kwargs)
        for ch in result.get("channels", []):
            if ch["name"] == channel_name:
                # 未参加なら参加
                if not ch.get("is_member"):
                    try:
                        client.conversations_join(channel=ch["id"])
                    except SlackApiError:
                        pass
                return ch["id"]
        cursor = result.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break
    return None


def fetch_new_messages(client: WebClient, channel_id: str, oldest: str) -> list[dict]:
    """指定タイムスタンプ以降の新着メッセージを取得"""
    messages = []
    cursor = None
    while True:
        kwargs = {"channel": channel_id, "oldest": oldest, "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        result = client.conversations_history(**kwargs)
        batch = result.get("messages", [])
        messages.extend(batch)
        cursor = result.get("response_metadata", {}).get("next_cursor", "")
        if not cursor or len(batch) < 200:
            break
    # 古い順にソート
    messages.sort(key=lambda m: float(m["ts"]))
    return messages


def download_slack_file(client: WebClient, file_info: dict, dest_dir: str) -> str | None:
    """Slack上のファイルをダウンロード"""
    url = file_info.get("url_private_download") or file_info.get("url_private")
    if not url:
        return None
    filename = file_info.get("name", "file")
    dest_path = os.path.join(dest_dir, filename)
    try:
        import requests as req
        resp = req.get(url, headers={"Authorization": f"Bearer {client.token}"})
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return dest_path
    except Exception as e:
        print(f"  ⚠️ ファイルダウンロード失敗: {filename} ({e})", file=sys.stderr)
        return None


# ============================================================
# メッセージ分類
# ============================================================

def classify_message(message: dict) -> str:
    """メッセージの種類を判定"""
    files = message.get("files", [])
    # bot のメッセージはスキップ（ファイル判定より先にチェック）
    if message.get("subtype") in ("bot_message", "channel_join") or message.get("bot_id"):
        return "skip"
    for f in files:
        mimetype = f.get("mimetype", "")
        if mimetype.startswith("image/"):
            return "business_card"
        if mimetype.startswith("audio/") or mimetype.startswith("video/"):
            return "voice_memo"
    # テキストがあればテキストメモ
    if message.get("text", "").strip():
        return "text_note"
    return "skip"


# ============================================================
# 構造化抽出: 名刺画像
# ============================================================

def process_business_card(
    gemini_client: genai.Client,
    slack_client: WebClient,
    file_info: dict,
) -> dict | None:
    """名刺画像をGemini Visionで構造化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = download_slack_file(slack_client, file_info, tmpdir)
        if not local_path:
            return None

        # Gemini Files API にアップロード
        uploaded = gemini_client.files.upload(file=local_path)

        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai_types.Content(
                    parts=[
                        genai_types.Part.from_uri(
                            file_uri=uploaded.uri,
                            mime_type=file_info.get("mimetype", "image/jpeg"),
                        ),
                        genai_types.Part.from_text(text=BUSINESS_CARD_PROMPT),
                    ]
                )
            ],
        )
        try:
            result = extract_json_from_text(response.text)
            result["type"] = "lead"
            return result
        except (ValueError, json.JSONDecodeError) as e:
            print(f"  ⚠️ 名刺解析エラー: {e}", file=sys.stderr)
            return None


# ============================================================
# 構造化抽出: 音声メモ
# ============================================================

def process_voice_memo(
    gemini_client: genai.Client,
    claude_client: anthropic.Anthropic,
    slack_client: WebClient,
    file_info: dict,
) -> dict | list | None:
    """音声メモをGeminiで文字起こし→Claudeで構造化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = download_slack_file(slack_client, file_info, tmpdir)
        if not local_path:
            return None

        # Step 1: Gemini Audio で文字起こし
        uploaded = gemini_client.files.upload(file=local_path)

        # 処理完了を待つ
        while uploaded.state.name == "PROCESSING":
            import time
            time.sleep(5)
            uploaded = gemini_client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            print(f"  ⚠️ 音声ファイルの処理に失敗", file=sys.stderr)
            return None

        transcription_response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai_types.Content(
                    parts=[
                        genai_types.Part.from_uri(
                            file_uri=uploaded.uri,
                            mime_type=file_info.get("mimetype", "audio/mp4"),
                        ),
                        genai_types.Part.from_text(
                            text="この音声を正確に文字起こししてください。話者が複数いる場合は区別してください。"
                        ),
                    ]
                )
            ],
        )
        transcript = transcription_response.text
        print(f"  📝 文字起こし完了（{len(transcript)}文字）")

        # Step 2: Claude で構造化
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = VOICE_MEMO_PROMPT.format(transcript=transcript, today=today)

        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return extract_json_from_text(response.content[0].text)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"  ⚠️ 音声メモ構造化エラー: {e}", file=sys.stderr)
            return None


# ============================================================
# 構造化抽出: テキストメモ
# ============================================================

def process_text_note(
    claude_client: anthropic.Anthropic,
    text: str,
    poster: str,
) -> dict | list | None:
    """テキストメモをClaudeで構造化"""
    today = datetime.now().strftime("%Y-%m-%d")
    prompt = TEXT_NOTE_PROMPT.format(text=text, poster=poster, today=today)

    response = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    try:
        return extract_json_from_text(raw)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"  ⚠️ テキスト構造化エラー: {e}", file=sys.stderr)
        print(f"  ⚠️ LLM応答: {raw[:300]}", file=sys.stderr)
        return None


# ============================================================
# Mazrica 書き込み
# ============================================================

def _resolve_contact(mc: MazricaClient, record: dict) -> tuple[int | None, int | None]:
    """
    氏名・部署・会社名からMazrica上の既存コンタクト/取引先を推定する。

    検索優先度:
      1. 会社名 + 部署 + 氏名 → 完全一致
      2. 会社名 + 氏名         → 同一取引先内で氏名一致
      3. 部署 + 氏名           → 会社名なしでもコンタクトから逆引き
      4. 氏名のみ              → 候補が1件なら採用

    Returns:
        (customer_id, contact_id) — 見つからなければ None
    """
    company_name = record.get("company_name", "")
    person_name = record.get("person_name", "")
    department = record.get("department", "")

    if not person_name:
        # 氏名なし → 会社名だけで取引先を返す
        if company_name:
            customers = mc.search_customers(company_name)
            if customers:
                return customers[0].get("id"), None
        return None, None

    # コンタクトを氏名で検索
    contacts = mc.search_contacts(name=person_name)

    if not contacts:
        # コンタクトが見つからない → 会社名があれば取引先だけ返す
        if company_name:
            customers = mc.search_customers(company_name)
            if customers:
                return customers[0].get("id"), None
        return None, None

    # --- 絞り込み ---

    # 会社名があれば、取引先名で絞り込む（必須フィルタ）
    if company_name:
        by_company = [
            c for c in contacts
            if company_name.lower() in (c.get("customer", {}).get("name", "") or "").lower()
        ]
        if not by_company:
            # 会社名が明示されているのに該当コンタクトなし → 新規扱い
            print(f"  🆕 既存コンタクトなし: {person_name} @ {company_name}（同名{len(contacts)}件は別会社）")
            customers = mc.search_customers(company_name)
            if customers:
                return customers[0].get("id"), None
            return None, None
        contacts = by_company

    # 部署があれば、部署名で絞り込む（あればより正確に）
    if department:
        by_dept = [
            c for c in contacts
            if department in (c.get("dept", "") or "")
        ]
        if by_dept:
            contacts = by_dept

    # 絞り込み結果
    if len(contacts) == 1:
        best = contacts[0]
        customer_id = best.get("customer", {}).get("id")
        contact_id = best.get("id")
        match_info = []
        if company_name:
            match_info.append(f"会社: {best.get('customer', {}).get('name', '?')}")
        if department:
            match_info.append(f"部署: {best.get('dept', '?')}")
        print(f"  🔍 コンタクト特定: {person_name}（{', '.join(match_info)}）→ ID: {contact_id}")
        return customer_id, contact_id

    if len(contacts) > 1:
        # 複数候補 → 部署でスコアリング（会社は既にフィルタ済み）
        if department:
            by_dept = [c for c in contacts if department in (c.get("dept", "") or "")]
            if len(by_dept) == 1:
                best = by_dept[0]
                customer_id = best.get("customer", {}).get("id")
                contact_id = best.get("id")
                cust_name = best.get("customer", {}).get("name", "?")
                print(f"  🔍 コンタクト特定（部署一致）: {person_name} @ {cust_name}（{department}）→ ID: {contact_id}")
                return customer_id, contact_id

        # それでも複数 → 特定できない、最初の候補の取引先だけ返す
        names = [f"{c.get('customer', {}).get('name', '?')}/{c.get('dept', '?')}" for c in contacts[:3]]
        print(f"  ⚠️ コンタクト候補が複数: {person_name} → {', '.join(names)}... 新規作成します")
        # 取引先だけは返す（コンタクトは新規作成）
        if company_name:
            customers = mc.search_customers(company_name)
            if customers:
                return customers[0].get("id"), None
        return None, None

    return None, None


def write_to_mazrica(mc: MazricaClient, record: dict) -> dict | None:
    """構造化レコードをMazricaに登録（既存チェック→新規 or 更新）。
    成功時は {"customer_id": ..., "contact_id": ...} を返す。"""
    company_name = record.get("company_name", "")
    person_name = record.get("person_name", "")

    if not company_name and not person_name:
        print("  ⚠️ 会社名・氏名ともにないためMazrica登録をスキップ", file=sys.stderr)
        return None

    # --- Step 1: 既存コンタクト/取引先の推定 ---
    customer_id, contact_id = _resolve_contact(mc, record)

    # --- Step 2: 取引先の作成 or 更新 ---
    try:
        if customer_id:
            # 既存取引先 → 情報があれば更新
            update_fields = {}
            if record.get("address"):
                update_fields["address"] = record["address"]
            if record.get("phone") and not person_name:
                update_fields["telNo"] = record["phone"]
            if record.get("url"):
                update_fields["webUrl"] = record["url"]
            if update_fields:
                mc.update_customer(customer_id, **update_fields)
            resolved_name = company_name or "(コンタクトから逆引き)"
            print(f"  📝 取引先 既存: {resolved_name}（ID: {customer_id}）")
        elif company_name:
            # 新規取引先
            result = mc.create_customer(
                name=company_name,
                address=record.get("address"),
                telNo=record.get("phone"),
                webUrl=record.get("url"),
            )
            customer_id = result.get("id")
            print(f"  ✅ 取引先 新規登録: {company_name}（ID: {customer_id}）")
        else:
            print("  ⚠️ 取引先を特定/作成できません（会社名なし・既存コンタクトなし）", file=sys.stderr)
            return None
    except MazricaAPIError as e:
        print(f"  ❌ 取引先登録エラー: {e}", file=sys.stderr)
        return None

    if not customer_id:
        return None

    # --- Step 3: コンタクトの作成 or 更新 ---
    if person_name:
        try:
            if contact_id:
                # 既存コンタクト → 情報があれば更新
                update_fields = {}
                if record.get("email"):
                    update_fields["email"] = record["email"]
                if record.get("phone"):
                    update_fields["tel"] = record["phone"]
                if record.get("title"):
                    update_fields["position"] = record["title"]
                if record.get("department"):
                    update_fields["dept"] = record["department"]
                if update_fields:
                    mc.update_contact(contact_id, **update_fields)
                print(f"  📝 コンタクト 更新: {person_name}（ID: {contact_id}）")
            else:
                # 新規コンタクト
                result = mc.create_contact(
                    name=person_name,
                    customer_id=customer_id,
                    email=record.get("email"),
                    tel=record.get("phone") or record.get("mobile"),
                    dept=record.get("department"),
                    position=record.get("title"),
                )
                contact_id = result.get("id")
                print(f"  ✅ コンタクト 新規登録: {person_name}（ID: {contact_id}）")
        except MazricaAPIError as e:
            print(f"  ❌ コンタクト登録エラー: {e}", file=sys.stderr)

    # --- Step 3: 案件の作成 or 更新（商談情報がある場合のみ） ---
    has_deal_info = record.get("deal_amount") or record.get("summary") or record.get("product")
    if has_deal_info and record.get("type") != "lead":
        deal_type_id = int(MAZRICA_DEAL_TYPE_ID) if MAZRICA_DEAL_TYPE_ID else None
        if not deal_type_id:
            print("  ⚠️ MAZRICA_DEAL_TYPE_ID 未設定のため案件登録をスキップ", file=sys.stderr)
        else:
            try:
                deal_name = f"{company_name} - {record.get('product', '案件')}"
                existing_deals = mc.search_deals(customer_id=customer_id)
                # 同一プロダクトの案件を検索
                matched_deal = None
                if record.get("product"):
                    for d in existing_deals:
                        if record["product"].lower() in d.get("name", "").lower():
                            matched_deal = d
                            break

                deal_kwargs = {}
                if record.get("deal_amount"):
                    deal_kwargs["amount"] = int(record["deal_amount"]) * 10000  # 万円→円
                if record.get("next_action_date"):
                    deal_kwargs["expectedContractDate"] = record["next_action_date"]

                if matched_deal:
                    mc.update_deal(matched_deal["id"], **deal_kwargs)
                    print(f"  📝 案件 更新: {matched_deal.get('name')}（ID: {matched_deal['id']}）")
                else:
                    mc.create_deal(
                        name=deal_name,
                        customer_id=customer_id,
                        deal_type_id=deal_type_id,
                        **deal_kwargs,
                    )
                    print(f"  ✅ 案件 新規登録: {deal_name}")
            except MazricaAPIError as e:
                print(f"  ❌ 案件登録エラー: {e}", file=sys.stderr)

    return {"customer_id": customer_id, "contact_id": contact_id}


# ============================================================
# Slack 確認返信
# ============================================================

def reply_confirmation(client: WebClient, channel_id: str, thread_ts: str, record: dict, mazrica_ids: dict | None = None):
    """処理結果をSlackスレッドに返信"""
    text = format_confirmation(record, mazrica_ids=mazrica_ids, app_url=MAZRICA_APP_URL)
    try:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=text,
        )
    except SlackApiError as e:
        print(f"  ⚠️ Slack返信失敗: {e.response['error']}", file=sys.stderr)


# ============================================================
# ユーザー名解決
# ============================================================

_user_cache: dict[str, str] = {}

def resolve_user_name(client: WebClient, user_id: str) -> str:
    """Slack ユーザーIDから表示名を取得"""
    if user_id in _user_cache:
        return _user_cache[user_id]
    try:
        result = client.users_info(user=user_id)
        profile = result["user"]["profile"]
        name = profile.get("real_name") or profile.get("display_name") or user_id
        _user_cache[user_id] = name
        return name
    except SlackApiError:
        return user_id


# ============================================================
# メイン処理
# ============================================================

def process_inbox(dry_run: bool = False, days: int | None = None):
    """CRM inbox を処理"""
    # --- バリデーション ---
    if not SLACK_BOT_TOKEN:
        print("エラー: SLACK_BOT_TOKEN が未設定です", file=sys.stderr)
        sys.exit(1)
    if not GOOGLE_API_KEY:
        print("エラー: GOOGLE_API_KEY が未設定です", file=sys.stderr)
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        print("エラー: ANTHROPIC_API_KEY が未設定です", file=sys.stderr)
        sys.exit(1)
    if not MAZRICA_API_KEY and not dry_run:
        print("エラー: MAZRICA_API_KEY が未設定です", file=sys.stderr)
        sys.exit(1)

    # --- クライアント初期化 ---
    slack_client = WebClient(token=SLACK_BOT_TOKEN)
    gemini_client = genai.Client(api_key=GOOGLE_API_KEY)
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    mc = None
    if not dry_run and MAZRICA_API_KEY:
        mc = MazricaClient(api_key=MAZRICA_API_KEY)

    # --- チャンネル検索 ---
    channel_id = find_channel_id(slack_client, CRM_INBOX_CHANNEL)
    if not channel_id:
        print(f"エラー: チャンネル #{CRM_INBOX_CHANNEL} が見つかりません", file=sys.stderr)
        print("  Slack で #crm-inbox チャンネルを作成してください", file=sys.stderr)
        sys.exit(1)

    print(f"📬 #{CRM_INBOX_CHANNEL} の処理を開始...")

    # --- 取得範囲の決定 ---
    if days:
        oldest = str((datetime.now() - timedelta(days=days)).timestamp())
    else:
        state = load_state()
        oldest = state.get("last_ts", "0")

    # --- メッセージ取得 ---
    messages = fetch_new_messages(slack_client, channel_id, oldest)
    if not messages:
        print("  新着メッセージなし")
        return

    print(f"  📨 {len(messages)}件の新着メッセージ")

    # --- 各メッセージを処理 ---
    processed = 0
    errors = 0
    latest_ts = oldest

    for msg in messages:
        msg_type = classify_message(msg)
        if msg_type == "skip":
            latest_ts = msg["ts"]
            continue

        ts = datetime.fromtimestamp(float(msg["ts"]))
        user_id = msg.get("user", "unknown")
        poster = resolve_user_name(slack_client, user_id)
        print(f"\n--- {ts.strftime('%m/%d %H:%M')} ({poster}) [{msg_type}] ---")

        record = None

        try:
            if msg_type == "business_card":
                for f in msg.get("files", []):
                    if f.get("mimetype", "").startswith("image/"):
                        record = process_business_card(gemini_client, slack_client, f)
                        break

            elif msg_type == "voice_memo":
                for f in msg.get("files", []):
                    mimetype = f.get("mimetype", "")
                    if mimetype.startswith("audio/") or mimetype.startswith("video/"):
                        record = process_voice_memo(
                            gemini_client, claude_client, slack_client, f
                        )
                        break

            elif msg_type == "text_note":
                record = process_text_note(claude_client, msg["text"], poster)

        except Exception as e:
            import traceback
            text_preview = msg.get("text", "")[:100]
            print(f"  ❌ 処理エラー: {e}")
            print(f"     入力テキスト: {text_preview}")
            print(f"     {traceback.format_exc().splitlines()[-1]}")
            errors += 1
            latest_ts = msg["ts"]
            continue

        # レコードが配列の場合（複数商談）
        records = record if isinstance(record, list) else [record] if record else []

        for rec in records:
            if not rec or rec.get("type") == "unknown":
                if not dry_run:
                    reply_confirmation(slack_client, channel_id, msg["ts"], rec or {"type": "unknown"})
                continue

            print(f"  → {json.dumps(rec, ensure_ascii=False)[:200]}")

            if not dry_run:
                # Mazrica に書き込み
                mazrica_ids = None
                if mc:
                    mazrica_ids = write_to_mazrica(mc, rec)
                # Slack に確認返信（Mazricaリンク付き）
                reply_confirmation(slack_client, channel_id, msg["ts"], rec, mazrica_ids)

            processed += 1

        latest_ts = msg["ts"]

    # --- 状態を保存 ---
    if not dry_run:
        save_state({"last_ts": latest_ts, "last_run": datetime.now().isoformat()})

    print(f"\n📊 処理完了: {processed}件登録 / {errors}件エラー / {len(messages)}件中")


def main():
    parser = argparse.ArgumentParser(description="CRM Inbox Processor")
    parser.add_argument("--dry-run", action="store_true", help="Sheets書き込み・Slack返信なし")
    parser.add_argument("--days", type=int, help="直近N日分を再処理")
    args = parser.parse_args()

    process_inbox(dry_run=args.dry_run, days=args.days)


if __name__ == "__main__":
    main()
