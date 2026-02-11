# CiviLink CS × Civil Engineer コンテキスト自動化環境

## 概要

CiviLinkのカスタマーサクセス兼Civilエンジニアとして、
顧客対応・技術支援・プロダクトフィードバックを横断的にこなすための
コンテキスト自動化環境です。

Cursor / Claude Code で使用することを想定。

## 自分の役割

**カスタマーサクセス（CS）として：**
- 顧客のオンボーディング支援・定着化
- 利用状況モニタリング・アクティブ率向上
- 技術的な問い合わせ対応（DocuWorks連携、ベクター表示等）
- 有償化に向けた顧客評価のサポート
- 顧客フィードバックのプロダクトチームへの還元

**Civilエンジニアとして：**
- 土木技術の専門知識を活かした顧客課題の理解
- PC橋設計・図面照査ワークフローの知見提供
- 技術的な導入障壁の特定と解決策の提案
- 設計基準・業務プロセスに基づく機能要望の整理

## ディレクトリ構成

```
civilink-cs/
├── README.md
├── .cursorrules
├── CLAUDE.md
│
├── context/                     # 自動同期コンテキスト
│   ├── slack/                   # Slack（直近3日分自動取得）
│   ├── calendar/                # Google Calendar同期
│   ├── meetings/                # MTG議事録
│   └── daily/                   # 日次サマリー
│
├── customers/                   # 顧客別コンテキスト ★CS業務の核
│   ├── README.md
│   ├── _template/               # 新規顧客テンプレート
│   ├── jrc/                     # JRC（有償化評価中）
│   └── ...                      # 他顧客
│
├── product/                     # プロダクト知識
│   ├── README.md
│   ├── features/                # 機能一覧・仕様
│   ├── release-notes/           # リリースノート
│   ├── known-issues/            # 既知の課題
│   ├── roadmap.md               # ロードマップ
│   └── competitive/             # 競合情報
│
├── technical/                   # 土木技術ナレッジ
│   ├── README.md
│   ├── docuworks/               # DocuWorks関連の技術知見
│   ├── drawing-workflow/        # 図面照査ワークフロー
│   ├── pc-bridge/               # PC橋設計知識
│   └── standards/               # 設計基準・規格
│
├── skills/                      # 業務スキル定義
│   ├── README.md
│   ├── 00-daily-start.md        # 始業チェック
│   ├── 01-customer-inquiry.md   # 顧客問い合わせ対応
│   ├── 02-onboarding.md         # オンボーディング支援
│   ├── 03-health-check.md       # 顧客ヘルスチェック
│   ├── 04-feature-request.md    # 機能要望整理
│   ├── 05-technical-investigation.md  # 技術調査
│   ├── 06-meeting-prep.md       # 顧客MTG準備
│   ├── 07-meeting-summary.md    # MTGサマリー・タスク抽出
│   └── 08-release-communication.md  # リリース案内作成
│
├── commands/                    # 自動化コマンド
│   ├── start-work.sh            # 始業
│   ├── end-work.sh              # 終業
│   └── setup.sh                 # 初期セットアップ
│
├── scripts/                     # 連携スクリプト
│   ├── slack_sync.py
│   ├── calendar_sync.py
│   └── task_extractor.py
│
└── tasks/                       # タスク管理
    ├── todo.md
    └── archive/
```

## セットアップ

```bash
chmod +x commands/*.sh
./commands/setup.sh
# → .env にSlack/Calendar APIトークンを設定
# → ./commands/start-work.sh で始業
```
