# CLAUDE.md - CiviLink CS × Civil Engineer

## このプロジェクトについて
CiviLinkのカスタマーサクセス兼Civilエンジニアの業務を自動化・効率化する環境。
Slack・Calendar・MTG議事録を自動同期し、顧客対応のコンテキストを常に最新に保つ。

## ディレクトリの役割
- `context/` - 自動同期される情報。Slack直近3日分、Calendar、MTG議事録。
- `customers/` - **最も重要**。顧客別の全情報。導入状況、課題、MTG履歴、意思決定ログ。
- `product/` - CiviLinkのプロダクト知識。機能仕様、リリースノート、既知課題。
- `technical/` - 土木技術ナレッジ。DocuWorks問題、図面照査フロー、設計基準。
- `skills/` - 業務スキル定義。顧客問い合わせ対応、ヘルスチェック、MTG準備等。
- `tasks/` - 自動抽出されたタスク。MTGやSlackから抽出。

## コマンド
- `./commands/start-work.sh` - 始業。Slack/Calendar同期→顧客アラート確認→タスク表示。
- `./commands/end-work.sh` - 終業。日次サマリー→タスクアーカイブ→Git Push。

## 主要顧客
- **JRC** - 有償化評価中。DocuWorksベクター表示が最大のボトルネック。小林さんが主要担当者。
- ユーザー別アクティブ数の追跡: https://docs.google.com/spreadsheets/d/17cNeY3cFlS9aPO3Bxt6Wihdw7Rst1pV35o1wxo00zek/

## 現在の重要課題
1. DocuWorksファイルのベクター表示（SDK制約で不可→PDF運用への移行を推進）
2. チーム（3名以上）運用組織の特定と有償化推進
3. 照査部門への導入（図面体験の向上がキー）

## 関連リソース
- DWとCLの対応表: https://docs.google.com/spreadsheets/d/1P9Y5BtnTTlysCUD77IY78D9oLD1ARiLYf_wwbzENZoM/
- DocuWorks整理ドキュメント: https://docs.google.com/document/d/1YSLUKvZdMdx77q26rtUqF6vf9atS_u7spw8SSALa0QU/
