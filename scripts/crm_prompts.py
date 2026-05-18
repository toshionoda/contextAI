"""
crm_prompts.py - CRM自動インプット用プロンプト定義

名刺画像・音声文字起こし・テキストメモから
顧客情報を構造化抽出するためのプロンプトを定義。
"""

# --- 名刺画像からの情報抽出 ---
# BUSINESS_CARD_PROMPT は .format() で使わないのでエスケープ不要

BUSINESS_CARD_PROMPT = """この名刺画像から情報を読み取り、以下のJSON形式で出力してください。
読み取れない項目はnullにしてください。推測はしないでください。

```json
{
  "company_name": "会社名",
  "department": "部署名",
  "title": "役職",
  "person_name": "氏名",
  "person_name_kana": "氏名カナ（読み取れる場合のみ）",
  "phone": "電話番号",
  "mobile": "携帯番号",
  "email": "メールアドレス",
  "address": "住所",
  "url": "ウェブサイト"
}
```

注意:
- 日本語の名刺が多い。漢字の氏名は正確に読み取ること
- 電話番号は半角ハイフン区切りで統一（例: 03-1234-5678）
- メールアドレスは正確に読み取ること（大文字小文字の区別は不要）
"""

# --- 音声文字起こしからの構造化 ---
# .format() で {transcript}, {today} を埋め込むため、JSON例の {{ }} をエスケープ

VOICE_MEMO_PROMPT = """以下は営業担当者の音声メモの文字起こしです。
商談・顧客接点に関する情報を抽出し、JSON形式で出力してください。
言及されていない項目はnullにしてください。推測はしないでください。

文字起こし:
{transcript}

```json
{{
  "type": "lead（新規リード） or update（既存顧客の更新）",
  "company_name": "会社名",
  "person_name": "担当者名",
  "title": "役職",
  "department": "部署",
  "phone": "電話番号",
  "email": "メールアドレス",
  "product": "関連プロダクト（CiviLink/VimSim/Gross/FDE/FrameWeb）",
  "deal_amount": "金額（数値。万円単位。例: 500）",
  "probability": "確度（%。例: 50）",
  "summary": "商談内容の要約（1〜2文）",
  "next_action": "ネクストアクション",
  "next_action_date": "期日（YYYY-MM-DD形式。相対日付は今日を基準に変換）",
  "source": "リード獲得経路（展示会/紹介/HP問い合わせ/電話/NJSS等）"
}}
```

注意:
- 「来週」「月末」等の相対日付は今日（{today}）を基準にYYYY-MM-DD形式に変換
- 金額は万円単位の数値のみ（「500万」→ 500）
- 複数の商談が含まれる場合、JSON配列で返す
"""

# --- テキストメモからの構造化 ---
# .format() で {text}, {poster}, {today} を埋め込むため、JSON例の {{ }} をエスケープ

TEXT_NOTE_PROMPT = """以下は営業担当者がSlackに投稿したテキストメモです。
商談・顧客接点に関する情報を抽出し、JSON形式で出力してください。
言及されていない項目はnullにしてください。推測はしないでください。

テキスト:
{text}

投稿者: {poster}

```json
{{
  "type": "lead（新規リード） or update（既存顧客の更新）",
  "company_name": "会社名",
  "person_name": "担当者名",
  "title": "役職",
  "department": "部署",
  "phone": "電話番号",
  "email": "メールアドレス",
  "product": "関連プロダクト（CiviLink/VimSim/Gross/FDE/FrameWeb）",
  "deal_amount": "金額（数値。万円単位。例: 500）",
  "probability": "確度（%。例: 50）",
  "summary": "商談内容の要約（1〜2文）",
  "next_action": "ネクストアクション",
  "next_action_date": "期日（YYYY-MM-DD形式。相対日付は今日を基準に変換）",
  "source": "リード獲得経路（展示会/紹介/HP問い合わせ/電話/NJSS等）"
}}
```

注意:
- 「来週」「月末」等の相対日付は今日（{today}）を基準にYYYY-MM-DD形式に変換
- 金額は万円単位の数値のみ（「500万」→ 500）
- 情報が少なすぎて構造化できない場合は {{"type": "unknown", "raw_text": "原文"}} を返す
- 複数の商談が含まれる場合、JSON配列で返す
"""

# --- Slack確認メッセージ生成 ---

def format_confirmation(record, mazrica_ids=None, app_url=""):
    """構造化レコードから Slack 返信用の確認メッセージを生成"""
    rec_type = record.get("type", "unknown")

    if rec_type == "unknown":
        return "⚠️ 情報が不足しているため登録できませんでした。会社名・担当者名を含めて再投稿してください。"

    parts = []
    label = "新規リード登録" if rec_type == "lead" else "商談更新"
    parts.append(f"✓ {label}")

    company = record.get("company_name")
    person = record.get("person_name")
    title = record.get("title")
    if company:
        name_str = company
        if person:
            name_str += f" {person}様"
            if title:
                name_str += f"（{title}）"
        parts.append(name_str)

    product = record.get("product")
    if product:
        parts.append(f"プロダクト: {product}")

    amount = record.get("deal_amount")
    prob = record.get("probability")
    if amount:
        amount_str = f"金額: {amount}万円"
        if prob:
            amount_str += f"（確度{prob}%）"
        parts.append(amount_str)

    summary = record.get("summary")
    if summary:
        parts.append(summary)

    next_action = record.get("next_action")
    next_date = record.get("next_action_date")
    if next_action:
        na_str = f"Next: {next_action}"
        if next_date:
            na_str += f"（{next_date}）"
        parts.append(na_str)

    phone = record.get("phone")
    email = record.get("email")
    contact_parts = []
    if phone:
        contact_parts.append(f"tel: {phone}")
    if email:
        contact_parts.append(f"email: {email}")
    if contact_parts:
        parts.append(" / ".join(contact_parts))

    # Mazrica リンク
    if mazrica_ids and app_url:
        links = []
        cid = mazrica_ids.get("customer_id")
        contact_id = mazrica_ids.get("contact_id")
        if cid:
            links.append(f"<{app_url}/customers/{cid}|取引先>")
        if contact_id:
            links.append(f"<{app_url}/contacts/{contact_id}|コンタクト>")
        if links:
            parts.append(f"Mazrica: {' / '.join(links)}")

    return "\n".join(parts)
