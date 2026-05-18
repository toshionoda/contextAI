# アタック準備

あなたはCiviLinkの営業支援として、攻略対象企業のブリーフィングを作成します。

## 引数
$ARGUMENTS にエリア名と会社名が含まれています。
例: "東北 pckk"、"関東 長大"
会社名のみの場合はエリアなしで検索してください。

## 実行手順

### Step 0: NJSSポテンシャルリスト確認
- `customers/njss/njss_potential_list.csv` をgrepで検索
- 「エリア」列でエリアを絞り、「落札会社名」列で会社名を部分一致検索
- ヒットした行の情報を抽出: 落札日、案件名、発注者、落札価格、支店名、ステータス、Malme担当
- エリア指定なしの場合は全エリアで検索
- CSVの列構成: エリア,No.,落札日,案件名,機関（発注者名）,落札会社名,落札価格（円）,支店名,電話番号,担当者,メールアドレス,Mazricaコンタクト,アプローチ方法,ステータス,最終接点日,Malme担当,アクション履歴

### Step 1: Mazrica APIから情報取得
以下のPythonコードで取引先・連絡先・案件を取得:
```python
import sys, os
sys.path.insert(0, 'mixpanel')
# .envを読み込み（inline comment対応）
env_path = 'mixpanel/mazrica/.env'
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            value = value.strip()
            if '#' in value: value = value[:value.index('#')].strip()
            if key.strip(): os.environ[key.strip()] = value
from mazrica.mazrica_client import MazricaClient
client = MazricaClient()
# 取引先検索 → 連絡先取得 → 案件取得
customers = client.search_customers("{会社名}")
if customers:
    contacts = client.get_contacts_by_customer(customers[0].id)
# BIM/CIM含む全案件を取引先名で取得
deals = client.get_deals_by_customer("{会社名}")
```
抽出する情報:
- 取引先: 名前、住所、電話番号
- 連絡先: 名前、役職、部署、メール、電話
- 案件（CiviLinkトライアル）: フェーズ、金額、担当者
- 案件（BIM/CIM受託）: 案件名、フェーズ、金額、担当者、受注予定日

### Step 1b: CSVで補完（Mazricaに無い情報）
- `customers/trial_organizations_enriched.csv` → 案件フェーズ、オーナー、Mazrica作成日
- `customers/CiviLinkトライアル（顧客リスト_VOC_開発要望） - Civilink_ユーザー.csv` → CiviLink登録ユーザー一覧

### Step 2: Slack検索（並列実行）
- `slack_search_public_and_private` で "{会社名}" を検索（limit:20, sort:timestamp, sort_dir:desc）
- 表記ゆれも試す（正式名、略称、英語名）
- `context/slack_summary/*.md` もgrepで直近の言及を補完

### Step 3: Notion検索（並列実行）
- `notion-search` で "{会社名}" をワークスペース全体検索
- `notion-query-meeting-notes` で会社名を含む議事録を検索
- ヒットしたページは `notion-fetch` で詳細取得
- `context/meetings/` と `context/notion/` 配下もgrepで確認

### Step 4: 顧客フォルダ確認
- `customers/{顧客名}/` が存在する場合はREADME.md・issues.md・meetings.mdを読む
- `customers/paid_status_analysis_2026-03-19.md` で有償化ステータス確認

### Step 5: ブリーフィング出力
以下のフォーマットで出力してください:

```
# アタックブリーフ: {会社名} ({エリア})
作成日: {本日の日付}

## 企業概要
- 正式名称:
- 業種:
- 当社との関係: {トライアル中/過去接点あり/新規}

## NJSSポテンシャルリスト
| 落札日 | 案件名 | 発注者 | 落札価格 | ステータス | Malme担当 |
|--------|--------|--------|---------|-----------|----------|
（NJSSリストから該当する案件。ヒットしない場合は「NJSSリスト該当なし」）

## 連絡先・担当者
| 名前 | 役職/部署 | メール | 備考 |
|------|----------|--------|------|
（CSVから抽出した連絡先）

## CiviLink案件状況
| 案件名 | フェーズ | 金額 | ユーザー数 | 受注予定日 |
|--------|---------|------|-----------|-----------|
（Mazrica案件データのうちCiviLink関連）

## BIM/CIM受託案件（Mazrica）
| 案件名 | フェーズ | 金額 | 担当 | 受注予定日 | 更新日 |
|--------|---------|------|------|-----------|--------|
（Mazrica案件データのうちBIM/CIM受託。CiviLink以外の案件を表示）

## 登録ユーザー
（CiviLinkに登録されているユーザー一覧）

## 社内コンテキスト

### Slackでの言及
（誰が・いつ・何を言っていたかの要約）

### MTG議事録・Notion
（過去の会議内容、関連ページの要約）

## 推奨アクション
- データから読み取れるアプローチ案
- 注意点・リスク
- 具体的な次のステップ
```

## 重要なルール
- 情報が見つからない場合は「データなし」と明記し、推測で埋めない
- .envファイルは絶対に読まない
- Step 1〜3は可能な限り並列で実行して速度を上げる
