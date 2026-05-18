# #dev-civilink-backend-notification - 直近3日分 (2026-04-27)

**04/24 10:59** (unknown): <!channel>
structuralengine/civilink-backend の `release` ブランチに新しいマイグレーションファイルが追加されました。
バックエンドを開発中の方は取り込みをお願いします。

**追加されたファイル:**
- alembic/versions/20260420_add_release_notes_tables.py

**04/24 18:35** (unknown): :warning: *バッチスクリプトが追加されました*

*PR:* <https://github.com/structuralengine/civilink-backend/pull/2286|[S52][feat][#2276] feat: backfill missing XDW conversions and PDF preview>
*追加者:* @minh-sora

*追加されたファイル:*
- `batchs/backfill_missing_pdf_previews.py`
- `batchs/backfill_missing_xdw_conversions.py`

@minh-sora :point_right: このスクリプトは本番デプロイ後に実行が必要ですか？
必要な場合は、実行タイミングと実行コマンドをこのスレッドに返信してください。

