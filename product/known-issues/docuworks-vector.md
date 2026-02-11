# 既知の課題: DocuWorksベクター表示

## 概要
DocuWorks（XDW）ファイルをCiviLink上でベクター表示できない。

## 影響
- JRC: 有償化のブロッカー
- DocuWorksを主要ファイル形式として使用する全顧客

## 原因
- DocuWorks SDK にベクター出力オプションが存在しない
- 画像形式（ラスター）での出力のみ対応

## 対応状況
- PDF向けベクター表示は 2025/11/05 にリリース済み
- DW向けは技術的に解決不可能（SDK制約）

## 回避策
- PDFに変換してからCiviLinkに投入
- 元のCAD/PDFファイルを直接利用

## 詳細
→ `technical/docuworks/README.md` を参照
