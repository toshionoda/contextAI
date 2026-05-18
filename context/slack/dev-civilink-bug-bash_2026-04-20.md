# #dev-civilink-bug-bash - 直近3日分 (2026-04-20)

**04/17 14:07** (USLACKBOT): <@U0AHL8GFAQY> が #dev-civilink-bug-bash に参加しました。これらのメンバーも Malme の新しいメンバーです。

**04/17 17:21** (U089CEHN71Q): <!here>
バグバッシュ定義を展開します。皆さんの意見を元にブラッシュアップしたいので返信ください。
とりあえず知見を貯めるところはSlackにしないとなと思っています

BugBash 提案 / BugBash Proposal
概要 / Overview
BugBashとは、チーム全員が通常の開発を止めて、集中的にバグの発見と修正に取り組むイベントです。
A BugBash is an event where the entire team pauses regular development to focus on finding and fixing bugs.

目的 / Purpose
エンジニアとして事業に貢献できることの一つとして、サービス運営に影響するバグ・不具合を減らす。 バグや不具合はサービス停止・機会損失につながり、売上や顧客の信頼に直結する。その意識をチーム全体で共有し、品質向上のための具体的なアクションとしてBugBashを実施する。
One of the ways engineers contribute to the business is by reducing bugs that impact service operations. Bugs lead to service outages, lost opportunities, and erosion of customer trust. BugBash is a concrete action to raise this awareness across the team and improve overall quality.

対象サービス / Target Services
• civilink-backend
• civilink-frontend
• civilink-comparison-service
• civilink-windows-server
• civilink-macro-server
• その他関連サービス / Other related services
ルール / Rules
1. バグ発見とバグ修正のそれぞれにポイント（PT）を付与し、合計PTで順位を決定する
2. 発見したバグはメモに記載し、先に記載した人が発見者となる
3. バグおよび改善系の報告を対象とする
4. リファクタリングはPT付与の対象外とする（別日に実施）
5. 修正完了後はコードレビュー＋テストを行い、PR状態で保留。翌日リリース判断を行う
6. Points (PT) are awarded for both finding and fixing bugs; total PT determines the ranking
7. Found bugs must be logged in a shared memo; the first to log it is credited as the finder
8. Bug reports and improvement suggestions are both eligible
9. Refactoring is not eligible for PT (to be scheduled separately)
10. After fixing, complete code review + testing and leave as a PR; release decision is made the next day
ポイント基準 / Point Criteria
   PT 基準 / Criteria     1 軽微・容易に発見できるもの / Minor, easily discoverable   2 中程度の影響があるもの / Moderate impact   3 サービスへの影響が大きいもの / High impact on service
修正フロー / Fix Flow
```バグ発見 → メモ記載 → GitHub Issue起票 → 修正 → コードレビュー → テスト → PR作成 → 翌日リリース判断
Bug found → Log in memo → Create GitHub Issue → Fix → Code review → Test → Create PR → Release decision next day```
リリース基準 / Release Criteria
BugBashでバグが発見された場合、そのバグに関連する修正が今週のスプリントで進行中であれば、該当PRは取り消し、翌日（水曜日）のリリースには含めない。修正は翌週のリリースまでに行い、改めてリリースする。
If a bug is found during BugBash and a related fix is already in progress within the current sprint, the corresponding PR must be reverted and excluded from the next day's (Wednesday) release. The fix should be reworked and included in the following week's release.

期待される効果 / Expected Outcomes
• 潜在的なバグの早期発見と対応 / Early detection and resolution of latent bugs
• サービス品質と安定性の向上 / Improved service quality and stability
• チーム全体の品質意識の向上 / Raised quality awareness across the team
• 普段触らない領域への理解促進 / Better understanding of unfamiliar areas of the codebase


**04/20 13:55** (U0ATJ20HK96): <@U0ATJ20HK96>さんがチャンネルに参加しました

