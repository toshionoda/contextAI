# AI データ基盤・ハーネスエンジニアリング 最新動向（2026年4月時点）

## 1. Anthropic / Claude — ハーネスエンジニアリング

「ハーネスエンジニアリング」は2026年初頭に主流化した概念。AIエージェントを本番環境で信頼性高く運用するための設計規律。

### 主な進展

- **Managed Agents（ベータ）** — Anthropicが提供するホスト型エージェント基盤。`managed-agents-2026-04-01` ベータヘッダーで利用可能。ファイル読み書き・コマンド実行・Web閲覧をセキュアな環境で実行
- **Brain / Hands / Session の分離設計** — エージェントの「脳（Claude+ハーネス）」「手（サンドボックス+ツール）」「セッション（イベントログ）」をインターフェースとして分離。それぞれ独立して差し替え・障害対応可能
- **作業エージェントと評価エージェントの分離** — 自己評価の問題を解決するために、作業するエージェントと判定するエージェントを分けるアプローチが有効
- **claude-progress.txt パターン** — git履歴と併用して長時間実行エージェントの作業状態を素早く把握する手法
- **4月のポリシー変更** — サードパーティ製ハーネス経由でのClaude Pro/Maxサブスクリプション利用をブロック開始

**重要な知見:** インフラ構成の違いだけで、エージェントコーディングベンチマークのスコアが数ポイント変動する（トップモデル間の差より大きい場合も）

### 参考リンク

- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Scaling Managed Agents: Decoupling the brain from the hands](https://www.anthropic.com/engineering/managed-agents)
- [Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [Claude Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview)

---

## 2. Google Cloud — データ基盤

### BigQuery

- **Legacy SQL廃止予告** — 2026年6月1日以降、使用実績がなければlegacy SQLが利用不可に
- **Geminiアシスタント強化** — BigQuery StudioでConversational Analytics（自然言語でデータ分析→SQL生成→可視化まで自動）
- **Continuous Queries** — BigQueryからSpannerへのリアルタイムストリーミングが可能に
- **課金変更** — 2026年2月1日からCloud Storageマルチリージョン転送に課金開始
- **アクセス制御** — 3月17日からBigQuery Data Transfer Serviceに新しいIAMポリシー権限が必要

### Vertex AI Agent Builder

- **Agent Engine Sessions & Memory Bank** がGA（一般提供）
- **Cloud API Registry（プレビュー）** — エージェントのMCPサーバーとツールの管理が可能に
- **Agent Engine Code Execution** がGA
- RAGエンジン: Cloud Storage, Google Drive, Slack, Jiraなど多様なデータソース接続

### 参考リンク

- [BigQuery release notes](https://docs.cloud.google.com/bigquery/docs/release-notes)
- [Vertex AI Agent Builder](https://cloud.google.com/products/agent-builder)

---

## 3. AWS — データ基盤

### ストレージ革新

- **S3 Vectors** — S3上で直接10億ベクトル埋め込みを保存・クエリ可能。専用ベクトルDBより最大90%コスト削減
- **S3オブジェクト上限50TB** — 従来の5TBから10倍に拡大（巨大なFM学習データセット向け）
- **アカウントレベル名前空間** — 他社と同名のバケットが作成可能に

### Bedrock Agents

- **Multi-Agent Collaboration** — 複数の専門エージェントがスーパーバイザーエージェントの調整下で協調動作
- **Custom Orchestration** — ユースケース固有のオーケストレーション（検証ステップ、マルチステッププロセス等）
- **AgentCore** — フレームワーク・モデル問わずエージェントをビルド・デプロイ・運用するプラットフォーム

### その他

- 2026年のCapEx予算 $2,000億（大半がデータセンター・カスタムチップ・AIインフラ）
- **EU Sovereign Cloud** を1月に開始（ドイツ法準拠、EU居住者のみ運用）
- 12以上のサービスを一斉廃止し、コアインフラ＋AIに投資集中

### 参考リンク

- [AWS in 2026: 5 Critical Updates](https://thinkmovesolutions.com/blogs/aws-in-2026-latest-services-updates/)
- [AWS Bedrock Agents](https://aws.amazon.com/bedrock/agents/)

---

## 4. AIスタートアップの淘汰

### ベクトルDB — 「ゴールドラッシュ」の終焉

- **Pinecone** — かつて$10億近い評価額だったが、2025年9月にCEO交代。独立継続に疑問符、買収先を探している状況
- **市場全体が「チェックボックス機能」化** — PostgreSQL（pgVector）、Elasticsearch、AWS S3 Vectorsが相次いでベクトル検索をネイティブ機能として追加
- **生き残り組**: Qdrantが$50MのシリーズB調達（2026年3月）、Milvus/Zillizも健在

> VentureBeatは「shiny object（流行りもの）からsober reality（冷静な現実）へ」と総括

### エージェントフレームワーク — 2強に収斂

| フレームワーク | GitHub Stars | ポジション |
|---|---|---|
| LangChain/LangGraph | 97,000+ | エコシステム最大。ツール統合+RAGに強み |
| CrewAI | 45,900+ | 最速成長。マルチエージェント協調に特化。日次1,200万実行 |
| AutoGen | — | Microsoft製。研究用途中心 |
| Dify | — | ノーコード/ローコード層で差別化 |

実務ではLangChain（ツール統合・RAG）+ CrewAI（マルチエージェント）の併用が定番パターン。

### ハードウェア/インフラ層

- Graphcore、Enfabrica、Celestial AI、Flex Logix など少なくとも6社がインカンベントに買収
- NvidiaがIllumexを$60Mで買収、Nebiusに$2B出資
- 98社中73社はまだ独立 → 本格的な淘汰はこれから

### 淘汰の構造

```
独立スタートアップ         → 大手プラットフォームに吸収
──────────────────────────────────────────────
Pinecone (ベクトルDB)      → AWS S3 Vectors, pgVector
専用RAGツール              → BigQuery Conversational Analytics
エージェントハーネス        → Anthropic Managed Agents, Bedrock AgentCore
チップ設計 (Graphcore等)    → Nvidia/AMD M&A
```

### 参考リンク

- [From shiny object to sober reality: The vector database story](https://venturebeat.com/ai/from-shiny-object-to-sober-reality-the-vector-database-story-two-years-later)
- [99% of AI Startups Will Be Dead by 2026](https://skooloflife.medium.com/99-of-ai-startups-will-be-dead-by-2026-heres-why-bfc974edd968)
- [Top AI Infrastructure Startups by Fundraising 2026](https://newmarketpitch.com/blogs/news/ai-infrastructure-top-startups-fundraising)

---

## 5. BIM/CIM × ベクトルDB

### 埋め込み対象の整理

| レイヤー | データ例 | 埋め込み方法 |
|---|---|---|
| メタデータ | IFCプロパティ（材質、寸法、工種、施工ステータス） | テキスト埋め込み（OpenAI text-embedding-3等） |
| ジオメトリ | 3D形状特徴（部材形状、トポロジー） | Deep Learning埋め込み（研究段階） |
| ドキュメント | 設計図書、照査コメント、施工記録 | テキスト埋め込み（チャンク分割+RAG） |
| 図面 | DocuWorks/PDF図面 | マルチモーダル埋め込み or OCR→テキスト |

### 業界で動いている事例

- **BIMConverse** — IFCに対して自然言語クエリを可能にするGraphRAGシステム
- **MCP4IFC** — LLMでIFCを操作するフレームワーク。ローカルベクトルストアからIFCドキュメント・コード例をRAG検索
- **OpenConstructionEstimate** — 建設コスト見積の55,000+作業項目をQdrantでベクトル管理。9言語対応

### ベクトルDB選定（淘汰トレンドを踏まえて）

| DB | 推奨度 | 強み | 懸念 |
|---|---|---|---|
| pgVector | ◎ | 既存DBに統合、運用シンプル、トランザクション | 大規模時の性能 |
| S3 Vectors | ◎ | 超低コスト、10億ベクトル、スケーラブル | AWS依存 |
| Qdrant | ○ | 検索性能最高、$50M調達済、RAG特化 | 独立系リスク |
| Pinecone | △ | 実績あり | 将来性に疑問、買収先探し中 |

### 実装アーキテクチャ案

```
┌─────────────────────────────────────────────┐
│  データ取り込み                                │
│                                              │
│  IFCファイル ──→ IfcOpenShell (解析)          │
│  DocuWorks  ──→ PDF変換 → テキスト抽出        │
│  設計図書    ──→ チャンク分割                   │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  埋め込み生成                                 │
│                                              │
│  テキスト → OpenAI text-embedding-3-large     │
│  IFCプロパティ → 構造化テキスト → 埋め込み      │
│  図面 → Claude Vision / OCR → 埋め込み        │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  PostgreSQL + pgVector                       │
│                                              │
│  projects (プロジェクト)                       │
│  components (部材: IFCメタ + embedding)        │
│  documents (図書チャンク + embedding)           │
│  reviews (照査記録 + embedding)                │
└──────────────┬──────────────────────────────┘
               ▼
┌─────────────────────────────────────────────┐
│  検索・活用                                   │
│                                              │
│  「この橋梁と似た構造の過去案件は？」            │
│  「耐震基準Aを満たす部材を検索」                │
│  「DocuWorks図面からコンクリート仕様を検索」     │
│  → セマンティック検索 + フィルタリング           │
└─────────────────────────────────────────────┘
```

### CiviLinkでのユースケース

1. **図面・DocuWorksの横断検索** — 「この断面形状に似た過去図面」をベクトル類似度で検索
2. **設計基準チェック** — 基準書をRAG化して、IFCモデルのプロパティと照合
3. **過去案件マッチング** — 新規案件の条件を入力→類似プロジェクトの設計・施工記録を自動提示
4. **照査支援** — 照査コメント履歴をベクトル化し、「過去に同様の指摘がなかったか」を検索

### 参考リンク

- [BIMConverse - GraphRAG for IFC](https://blog.iaac.net/bimconverse-graphrag-for-ifc-natural-language-queries/)
- [MCP4IFC: IFC-Based Building Design using LLMs](https://arxiv.org/html/2511.05533v1)
- [OpenConstructionEstimate - Qdrant vector DB](https://github.com/datadrivenconstruction/OpenConstructionEstimate-DDC-CWICR)
- [Intelligent BIM Searching via Deep Embedding](https://www.mdpi.com/2075-5309/15/6/951)
- [BIM and IFC Data Readiness for AI](https://www.mdpi.com/2075-5309/14/10/3305)

---

*調査日: 2026-04-09*
