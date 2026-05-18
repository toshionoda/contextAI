#!/usr/bin/env python3
"""
トライアル組織一覧にアカウント作成日・分野・失注フラグを付与するスクリプト

データソース:
  - 案件一覧CSV (Mazrica): customers/CiviLinkトライアル（顧客リスト_VOC_開発要望） - 案件一覧.csv
  - CS-Panel UserList: mixpanel/data/CS-Panel - UserList (2).csv
"""

import csv
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent

# --- ファイルパス ---
TRIAL_CSV = BASE_DIR / "customers" / "CiviLinkトライアル（顧客リスト_VOC_開発要望） - 案件一覧.csv"
# submodule内にデータがない場合は元ディレクトリを参照
CSPANEL_CSV_SUBMODULE = BASE_DIR / "mixpanel" / "data" / "CS-Panel - UserList (2).csv"
CSPANEL_CSV_ORIGINAL = Path.home() / "Documents" / "mixpanel" / "data" / "CS-Panel - UserList (2).csv"
CSPANEL_CSV = CSPANEL_CSV_SUBMODULE if CSPANEL_CSV_SUBMODULE.exists() else CSPANEL_CSV_ORIGINAL
OUTPUT_CSV = BASE_DIR / "customers" / "trial_organizations_enriched.csv"


def normalize_company_name(name: str) -> str:
    """会社名を正規化して比較しやすくする"""
    name = name.strip()
    # 全角→半角スペース
    name = name.replace("\u3000", " ")
    # カッコ表記の統一
    name = name.replace("（", "(").replace("）", ")")
    name = name.replace("(株)", "").replace("㈱", "")
    name = name.replace("株式会社", "").replace("(株）", "")
    # スペース除去
    name = re.sub(r"\s+", "", name)
    # 「株式会社」の前後位置を無視するため除去済み
    return name


def load_cspanel_org_info() -> dict:
    """CS-Panel CSVから組織名→アカウント作成日・部署別オーナー情報を取得"""
    org_info = {}
    with open(CSPANEL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            org_name = row.get("組織名", "").strip()
            date_str = row.get("アカウント作成日", "").strip()
            if not org_name or not date_str:
                continue
            # テスト/デモ組織を除外
            if any(kw in org_name for kw in ["テスト", "test", "デモ", "DEMO", "Malme", "動画", "PROD", "橋田"]):
                continue
            try:
                dt = datetime.strptime(date_str, "%Y/%m/%d %H:%M")
            except ValueError:
                continue
            normalized = normalize_company_name(org_name)
            contractor = row.get("契約者名", "").strip()
            org_email = row.get("組織メールアドレス", "").strip()
            dept = row.get("部署名", "").strip()
            user_name = row.get("ユーザー名", "").strip()
            user_email = row.get("ユーザーメールアドレス", "").strip()
            role = row.get("権限", "").strip()

            if normalized not in org_info:
                org_info[normalized] = {
                    "dt": dt,
                    "date_str": dt.strftime("%Y/%m/%d"),
                    "original_name": org_name,
                    "contractor": contractor,
                    "org_email": org_email,
                    "departments": {},  # 部署名 → {contractor, org_email, org_name}
                    "users": [],  # 全ユーザーリスト（重複排除用）
                }
            elif dt < org_info[normalized]["dt"]:
                org_info[normalized]["dt"] = dt
                org_info[normalized]["date_str"] = dt.strftime("%Y/%m/%d")

            # 部署ごとのオーナー（権限=オーナー or 契約者）を記録
            if dept and dept not in org_info[normalized]["departments"]:
                org_info[normalized]["departments"][dept] = {
                    "contractor": contractor,
                    "org_email": org_email,
                    "org_name": org_name,
                    "dept": dept,
                }

            # ユーザーを記録（重複排除のフォールバック用）
            if user_name and user_email:
                existing_emails = {u["email"] for u in org_info[normalized]["users"]}
                if user_email not in existing_emails:
                    org_info[normalized]["users"].append({
                        "name": user_name,
                        "email": user_email,
                        "dept": dept,
                        "role": role,
                    })
    return org_info


def match_org_name(trial_name: str, cspanel_orgs: dict) -> Optional[str]:
    """トライアルの取引先名とCS-Panelの組織名をファジーマッチング"""
    normalized_trial = normalize_company_name(trial_name)

    # 完全一致
    if normalized_trial in cspanel_orgs:
        return normalized_trial

    # 部分一致（どちらかが含む）
    for key in cspanel_orgs:
        if normalized_trial in key or key in normalized_trial:
            if len(min(normalized_trial, key, key=len)) >= 3:  # 最低3文字以上の一致
                return key

    return None


def classify_field(company_name: str) -> str:
    """会社名から分野を推定"""
    name = company_name

    # 具体的な会社名による分類（パターンマッチより優先）
    specific_map = {
        "不動テトラ": "ゼネコン",
        "村本建設": "ゼネコン",
        "矢作建設": "ゼネコン",
        "伊藤組土建": "ゼネコン",
        "戸田建設": "ゼネコン",
        "青木あすなろ建設": "ゼネコン",
        "オリエンタル白石": "ゼネコン",
        "川田工業": "ゼネコン",
        "望月鉄工所": "ゼネコン",
        "手塚組": "ゼネコン",
        "藤原組": "ゼネコン",
        "草野作工": "ゼネコン",
        "中原建設": "ゼネコン",
        "大進": "ゼネコン",
        "ワキタCSS技術開発": "ゼネコン",
        "応用地質": "地質・調査",
        "アジア航測": "地質・調査",
        "森林総合コンサルタント": "森林・林業",
        "ふたば": "建設コンサル",
        "ウヌマ地域総研": "建設コンサル",
        "日本工営": "建設コンサル",
        "長大": "建設コンサル",
        "キタック": "建設コンサル",
        "ドーコン": "建設コンサル",
        "パシフィックコンサルタンツ": "建設コンサル",
        "NiX JAPAN": "建設コンサル",
        "いであ": "建設コンサル",
        "オオバ": "建設コンサル",
        "日本水工設計": "建設コンサル",
        "建設技術研究所": "建設コンサル",
    }
    for key, field in specific_map.items():
        if key in name:
            return field

    # パターンマッチ
    patterns = [
        (r"コンサルタン[ツト]|コンサル|設計|技研|エンジニアリング|エンジニヤリング|技術開発|技術研究", "建設コンサル"),
        (r"建設|組$|工業|鉄工|土建|白石", "ゼネコン"),
        (r"地質|航測|測量", "地質・調査"),
        (r"森林|林業", "森林・林業"),
    ]
    for pattern, field in patterns:
        if re.search(pattern, name):
            return field

    return "その他"


def enrich_trial_list():
    """メイン処理：トライアル一覧を整理"""
    # CS-Panelの組織情報を読み込み
    cspanel_orgs = load_cspanel_org_info()
    print(f"CS-Panel組織数: {len(cspanel_orgs)}")

    # 案件一覧を読み込み
    rows = []
    with open(TRIAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"案件数: {len(rows)}")

    # 取引先名でユニーク化（同じ取引先の複数案件をまとめる）
    org_cases = {}
    for row in rows:
        company = row["取引先"].strip()
        if company not in org_cases:
            org_cases[company] = []
        org_cases[company].append(row)

    print(f"ユニーク取引先数: {len(org_cases)}")

    # 出力用データを作成
    enriched = []
    matched_count = 0
    unmatched = []
    today = datetime(2026, 3, 14)

    # 同一組織の案件に部署別オーナーを順番に割り当てるためのカウンター
    org_dept_index = {}  # normalized_key → 次に使う部署インデックス
    used_owners = set()  # 既に割り当て済みのオーナー名（重複回避用）

    for row in rows:
        company = row["取引先"].strip()
        phase = row.get("フェーズ", "").strip()
        contract = row.get("契約方法", "").strip()
        area = row.get("エリア", "").strip()
        user_count = row.get("ユーザー数", "").strip()
        created_at = row.get("作成日時", "").strip()
        deal_name = row.get("案件名", "").strip()
        close_date = row.get("受注予定日", "").strip()

        # アカウント作成日・オーナー情報をマッチング
        match_key = match_org_name(company, cspanel_orgs)
        account_created = ""
        owner_name = ""
        owner_email = ""
        dept_name = ""
        if match_key:
            org = cspanel_orgs[match_key]
            account_created = org["date_str"]
            depts = list(org["departments"].values())
            users = org.get("users", [])

            if len(depts) > 1:
                # 複数部署がある場合、未使用のオーナーを優先的に割り当て
                assigned = False
                idx = org_dept_index.get(match_key, 0)
                # まず未使用のオーナーを探す
                for i in range(len(depts)):
                    candidate = depts[(idx + i) % len(depts)]
                    if candidate["contractor"] not in used_owners:
                        owner_name = candidate["contractor"]
                        owner_email = candidate["org_email"]
                        dept_name = candidate["dept"]
                        org_dept_index[match_key] = (idx + i + 1) % len(depts)
                        assigned = True
                        break
                if not assigned:
                    # 全部署のオーナーが使用済み → ユーザーから未使用の人を探す
                    for u in users:
                        if u["name"] not in used_owners:
                            owner_name = u["name"]
                            owner_email = u["email"]
                            dept_name = u["dept"]
                            assigned = True
                            break
                if not assigned:
                    # フォールバック: ラウンドロビン
                    dept_info = depts[idx % len(depts)]
                    owner_name = dept_info["contractor"]
                    owner_email = dept_info["org_email"]
                    dept_name = dept_info["dept"]
                    org_dept_index[match_key] = idx + 1
            else:
                # 部署1つの場合もユーザーで分散
                if org["contractor"] in used_owners and users:
                    for u in users:
                        if u["name"] not in used_owners:
                            owner_name = u["name"]
                            owner_email = u["email"]
                            dept_name = u.get("dept", "")
                            break
                    else:
                        owner_name = org["contractor"]
                        owner_email = org["org_email"]
                        if depts:
                            dept_name = depts[0]["dept"]
                else:
                    owner_name = org["contractor"]
                    owner_email = org["org_email"]
                    if depts:
                        dept_name = depts[0]["dept"]

            if owner_name:
                used_owners.add(owner_name)
            matched_count += 1
        else:
            if company not in [u[0] for u in unmatched]:
                unmatched.append((company, normalize_company_name(company)))

        # 分野を推定
        field = row.get("分野", "").strip()
        if not field:
            field = classify_field(company)

        # 失注理由フラグ
        lost_reason = row.get("失注理由", "").strip()
        if not lost_reason and phase == "内示":
            # 受注予定日を過ぎているか確認
            if close_date:
                try:
                    close_dt = datetime.strptime(close_date, "%Y-%m-%d")
                    if close_dt < today:
                        lost_reason = "要確認（期限超過）"
                except ValueError:
                    pass

        enriched.append({
            "取引先": company,
            "案件名": deal_name,
            "オーナーアカウント": owner_name,
            "オーナーメール": owner_email,
            "部署名": dept_name,
            "アカウント作成日": account_created,
            "分野": field,
            "エリア": area,
            "ユーザー数": user_count,
            "期間": row.get("期間", "").strip(),
            "フェーズ": phase,
            "契約方法": contract,
            "案件金額": row.get("案件金額", "").strip(),
            "受注予定日": close_date,
            "Mazrica作成日": created_at[:10] if created_at else "",
            "失注理由": lost_reason,
            "担当者": row.get("担当者", "").strip(),
            "オーナー重複": "",
        })

    # オーナーアカウントの重複チェック
    owner_counts = {}
    for r in enriched:
        name = r["オーナーアカウント"]
        if name:
            owner_counts[name] = owner_counts.get(name, 0) + 1
    for r in enriched:
        name = r["オーナーアカウント"]
        if name and owner_counts.get(name, 0) > 1:
            r["オーナー重複"] = "重複"

    # CSV出力
    fieldnames = [
        "取引先", "案件名", "オーナーアカウント", "オーナーメール", "部署名",
        "オーナー重複", "アカウント作成日", "分野", "エリア",
        "ユーザー数", "期間", "フェーズ", "契約方法", "案件金額",
        "受注予定日", "Mazrica作成日", "失注理由", "担当者",
    ]
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)

    # サマリー出力
    print(f"\n=== 結果サマリー ===")
    print(f"出力先: {OUTPUT_CSV}")
    print(f"全案件数: {len(enriched)}")
    print(f"アカウント作成日マッチ: {matched_count}/{len(enriched)} ({matched_count*100//len(enriched)}%)")

    # 分野別集計
    field_counts = {}
    for r in enriched:
        f = r["分野"] or "未分類"
        field_counts[f] = field_counts.get(f, 0) + 1
    print(f"\n--- 分野別集計 ---")
    for f, c in sorted(field_counts.items(), key=lambda x: -x[1]):
        print(f"  {f}: {c}件")

    # フェーズ別集計
    phase_counts = {}
    for r in enriched:
        p = r["フェーズ"] or "不明"
        phase_counts[p] = phase_counts.get(p, 0) + 1
    print(f"\n--- フェーズ別集計 ---")
    for p, c in sorted(phase_counts.items(), key=lambda x: -x[1]):
        print(f"  {p}: {c}件")

    # 失注理由フラグ
    lost_count = sum(1 for r in enriched if r["失注理由"])
    print(f"\n--- 失注理由フラグ ---")
    print(f"  要確認: {lost_count}件")

    # マッチしなかった組織
    if unmatched:
        print(f"\n--- アカウント作成日が未マッチの取引先 ({len(unmatched)}件) ---")
        for name, normalized in unmatched:
            print(f"  {name}")


if __name__ == "__main__":
    enrich_trial_list()
