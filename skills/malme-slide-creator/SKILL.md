---
name: malme-slide-creator
description: "Malmeブランドのプレゼンテーション作成ツール。提案書・サービス紹介・会社概要スライドの新規作成、既存PPTXテンプレートのテキスト置換・スライド並べ替え・複製に対応。コンテンツに基づき最適なスライド枚数とレイアウトを自動決定する。"
---

# Malme スライドクリエイター

Malmeコーポレートブランディングを使用したプロフェッショナルなPowerPointプレゼンテーション作成。

## ブランドガイドライン

### カラー
| 用途 | 値 | PptxGenJS |
|-----|-----|-----------|
| プライマリ | `#3C3838` (ウォームチャコール) | `3C3838` |
| アクセント | `#C2706B` (ダスティローズ) | `C2706B` |
| グラデーション | `#F5EAEA` → `#EACED0` | - |
| テキスト(濃/淡) | `#333333` / `#FFFFFF` | - |
| アクセントグレー | `#F5F0F0` | - |

**チャートカラー**: `["3C3838", "C2706B", "E8B4B0", "8A7C7C", "5C4848"]`

### アセット
- **ロゴ(黒)**: `assets/malme-logo.png` (全スライド共通、右上、幅60-80pt)
- **ロゴ(白)**: `assets/malme_logo_white.svg` (暗い背景に配置する場合のみ使用)
- **背景**: `assets/slide-background.png` (タイトル/クロージング用)

### タイポグラフィ
| 要素 | フォント | サイズ |
|-----|---------|-------|
| タイトル見出し | Meiryo Bold | 32-40pt |
| セクションヘッダー(h2) | Meiryo Bold | 20-24pt |
| コンテンツ見出し(h3) | Meiryo Bold | 16-20pt |
| 本文/箇条書き | Meiryo | 14-18pt |

**サイズ選択**: 情報量少(3-5項目)→大きめ(18pt)、情報量多(8項目以上)→14-16pt、高密度テーブル→10-12pt

## ワークフロー

**確認原則**: 方針に迷う場合や入力情報に不明瞭な点がある場合は、推測で進めず、遠慮なくユーザーに質問すること。

### 1. コンテンツ分析
- プレゼンタイプ: 提案書/サービス紹介/会社概要/レポート
- キーメッセージ: 3-5個抽出
- スライド枚数: 5-15枚(コンテンツ深度による)

### 2. 構成計画
```
1: タイトル(背景付) → 2: アジェンダ → 3-N: コンテンツ → N+1: サマリー → N+2: クロージング(背景付)
```

### 3. 技術リファレンス
**必須**: [html2pptx.md](references/html2pptx.md) を読み込むこと。

### 4. HTMLスライド作成

**基本ルール**:
- サイズ: `width: 720pt; height: 405pt` (16:9)
- テキストは `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` 内に配置
- テーブルは `<table>`, `<tr>`, `<th>`, `<td>` で構造化（自動変換対応）
- チャートエリア: `class="placeholder"`
- CSSグラデーション: Sharpで事前PNG化必須

## スライドテンプレート

詳細なHTMLテンプレートとコード例は [templates.md](references/templates.md) を参照。

### テンプレート一覧（概要）

| タイプ | 用途 | 参照 |
|-------|------|------|
| タイトル | 背景画像付き開始スライド | [templates.md#タイトルスライド](references/templates.md#タイトルスライド) |
| コンテンツ | 箇条書き・本文 | [templates.md#コンテンツスライド](references/templates.md#コンテンツスライド箇条書き) |
| 2カラム | 比較・並列情報 | [templates.md#2カラム](references/templates.md#2カラムレイアウト) |
| 3カラム | 3つの並列要素 | [templates.md#3カラム](references/templates.md#3カラムレイアウト) |
| データ/チャート | チャートプレースホルダー付き | [templates.md#データ](references/templates.md#データチャートスライド) |
| 高密度2カラム | 技術レポート・大量情報 | [templates.md#高密度](references/templates.md#情報密度の高い2カラム) |
| テーブル | 比較表・データテーブル | [templates.md#テーブル](references/templates.md#テーブルスライド) |
| クロージング | 背景画像付き終了スライド | [templates.md#クロージング](references/templates.md#クロージングスライド) |

### レイアウト選択ガイド

| コンテンツ | テンプレート | フォント |
|----------|------------|---------|
| 3-5項目 | コンテンツスライド | 18pt |
| 4-8項目(2列) | 2カラム | 16pt |
| 8項目以上 | 高密度2カラム | 9-11pt |
| 比較表(5行以下) | テーブル | 14pt |
| 比較表(6行以上) | テーブル高密度 | 10-12pt |

**オーバーフロー防止**: 詳細は [templates.md#オーバーフロー防止ガイド](references/templates.md#オーバーフロー防止ガイド) を参照

## 検証

```bash
python scripts/thumbnail.py output.pptx workspace/thumbnails --cols 4
```
確認: テキスト切れ、ロゴ配置、色の一致、マージン(端から最小30pt)

## スライドタイプ

| タイプ | ヘッダー | 用途 |
|------|--------|------|
| タイトル/クロージング | 背景画像 | 開始/終了 |
| その他全て | 白背景＋アクセントライン(#C2706B) | コンテンツ |

## 依存関係

### セットアップ（プロジェクトルートで実行）
```bash
# Node.js依存関係
npm install pptxgenjs playwright sharp

# Playwrightブラウザ
npx playwright install chromium

# Python依存関係（オプション）
pip install python-pptx Pillow lxml
```

**npm**: pptxgenjs, playwright, sharp
**Python**: python-pptx, Pillow, lxml
**システム**: soffice (LibreOffice), pdftoppm (Poppler)

### トラブルシューティング（コンテナ環境）

Claudeブラウザ版などのコンテナ環境では、Playwrightのバージョンとプリインストール済みChromiumのバージョンを一致させる必要がある。

```bash
# プリインストール済みChromiumのバージョン確認
ls /opt/pw-browsers/ 2>/dev/null || ls ~/.cache/ms-playwright/ 2>/dev/null

# 例: chromium-1194 がある場合 → playwright@1.56.0 を使用
npm install playwright@1.56.0
```

| Chromiumビルド | 対応Playwright |
|---------------|---------------|
| 1194 | 1.56.x |
| 1208 | 1.58.x |

`html2pptx.js` は非macOS環境で自動的に `--no-sandbox`, `--disable-dev-shm-usage` 等のフラグを付与する。

---

# テンプレート編集機能

## OOXMLダイレクト編集

**必須**: [ooxml.md](references/ooxml.md) 参照

```bash
# 展開 → 編集 → 検証 → パック
python ooxml/scripts/unpack.py template.pptx workspace/unpacked
python ooxml/scripts/validate.py workspace/unpacked --original template.pptx
python ooxml/scripts/pack.py workspace/unpacked output.pptx
```

## テキスト置換

```bash
python scripts/replace.py input.pptx output.pptx "{{placeholder}}" "値"
python scripts/replace.py input.pptx output.pptx --mapping replacements.json
```

## スライド操作

```bash
python scripts/rearrange.py in.pptx out.pptx --move 3 1      # 移動
python scripts/rearrange.py in.pptx out.pptx --duplicate 2 4  # 複製
python scripts/rearrange.py in.pptx out.pptx --delete 5 6     # 削除
```

## ツールリファレンス

| ツール | 用途 |
|-------|------|
| `ooxml/scripts/unpack.py` | PPTX展開 |
| `ooxml/scripts/pack.py` | PPTX作成 |
| `ooxml/scripts/validate.py` | 構造検証 |
| `scripts/replace.py` | テキスト置換 |
| `scripts/rearrange.py` | スライド操作 |
| `scripts/inventory.py` | コンテンツ分析 |

主要XMLファイルやOOXML構造の詳細は [ooxml.md](references/ooxml.md) を参照。

## 出力後処理（軽量版）

案件フォルダ（番号付きフォルダ 00-〜99- 配下）にファイルを出力した場合のみ実行:

- [ ] CLAUDE.md「ドキュメント最新版」テーブルの該当カテゴリ行を更新
- [ ] docs/CHANGELOG.md に ad-hoc エントリを追記

詳細: [context-awareness-rules.md](../references/context-awareness-rules.md)

※ ステークホルダー検出・整合性チェック等は不要（PMスキルの完全版後処理とは異なる）
