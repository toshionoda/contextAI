# DocuWorks × CiviLink 技術知見

## 問題の概要
CiviLink上でDocuWorks（XDW）ファイルのベクター表示ができない。
PDF向けのベクター表示機能は2025/11/5にリリース済みだが、DWファイルには適用不可。

## 技術調査結果（2024/12 Hashida調査）

| 調査項目 | 結果 |
|---------|------|
| DocuWorks SDK API | ベクター出力オプション**なし**（画像形式のみ） |
| 仮想プリンタ方式 | A3/A4混在文書が全てA4出力される → **不可** |
| API仕様書再確認 | ベクター出力は**サポートされていない** |

## 代替アプローチ

| 案 | 概要 | 実現可能性 | 推奨度 |
|---|------|-----------|--------|
| A | DW文書からオリジナルデータ（元CAD/PDF）を抽出 | ★★★ | **要確認** |
| B | DocuWorks PDF Creator + RPA自動化 | ★★☆ | 低 |
| C | 元CAD/PDFファイルを直接CiviLinkに投入 | ★★★★ | **推奨（中長期）** |
| D | DocuWorks Viewer Light埋め込み | ★★☆ | 要調査 |
| E | XDWファイル直接パース | ★☆☆ | 非現実的 |

## 顧客がDocuWorksを使う理由
- 機能面が多い
- ファイル容量が軽い
- ※必ずしもDocuWorksでなければならないわけではない（JRC）

## 現在の方針
- **短期**: PDFでの運用を促す
- **中長期**: DWを介在させないワークフロー構築
- **確認事項**: JRCのDW文書にオリジナルデータが添付されているか

## 関連リソース
- DWとCLの対応表: https://docs.google.com/spreadsheets/d/1P9Y5BtnTTlysCUD77IY78D9oLD1ARiLYf_wwbzENZoM/
- DocuWorks整理ドキュメント: https://docs.google.com/document/d/1YSLUKvZdMdx77q26rtUqF6vf9atS_u7spw8SSALa0QU/

## 教訓
- SDKの制約は回避できない。SDK開発を自分たちでやるのは非現実的。
- 「DW撲滅」は顧客への影響が大きすぎる → 段階的移行が現実的。
- 照査部門への導入には「数百枚をノンストレスで見る体験」が必須。
