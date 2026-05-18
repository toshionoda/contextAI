# Malme HTMLスライドテンプレート詳細

Malmeブランドに準拠したHTMLスライドの詳細テンプレート集。

## 目次

1. [共通CSS基盤](#共通css基盤)
2. [タイトルスライド](#タイトルスライド)
3. [コンテンツスライド（箇条書き）](#コンテンツスライド箇条書き)
4. [2カラムレイアウト](#2カラムレイアウト)
5. [3カラムレイアウト](#3カラムレイアウト)
6. [データ/チャートスライド](#データチャートスライド)
7. [情報密度の高い2カラム](#情報密度の高い2カラム)
8. [テーブルスライド](#テーブルスライド)
9. [クロージングスライド](#クロージングスライド)
10. [オーバーフロー防止ガイド](#オーバーフロー防止ガイド)
11. [レイアウト選択ガイド](#レイアウト選択ガイド)

---

## 共通CSS基盤

全テンプレートで以下を基盤として使用:

```css
body {
  width: 720pt;
  height: 405pt;
  margin: 0;
  padding: 0;
  font-family: 'Meiryo', Arial, sans-serif;
  display: flex;
  flex-direction: column;
}
.header {
  background: #FFFFFF;
  padding: 12pt 30pt;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 3px solid #C2706B;
}
.header h2 {
  color: #3C3838;
  font-size: 22pt;
  margin: 0;
  font-weight: bold;
}
.logo { height: 28pt; }
.content { margin: 20pt 40pt; flex: 1; }
h3 {
  color: #333333;
  font-size: 20pt;
  margin: 0 0 15pt 0;
  font-weight: bold;
}
```

---

## タイトルスライド

背景画像付きの開始スライド。

```html
<style>
body { background-image: url('assets/slide-background.png'); background-size: cover; }
.content { margin: 80pt 50pt; justify-content: center; }
.logo { position: absolute; top: 20pt; right: 30pt; width: 80pt; }
h1 { color: #333333; font-size: 40pt; margin: 0 0 20pt 0; }
p.subtitle { color: #C2706B; font-size: 20pt; margin: 0; }
p.date { color: #666666; font-size: 14pt; margin-top: 30pt; }
</style>
<body>
<img class="logo" src="assets/malme-logo.png">
<div class="content">
  <h1>プレゼンテーションタイトル</h1>
  <p class="subtitle">サブタイトル</p>
  <p class="date">2026.01.21</p>
</div>
</body>
```

---

## コンテンツスライド（箇条書き）

標準的な箇条書きコンテンツ用。

```html
<!-- 共通CSS基盤 + 以下 -->
<style>
h3 { color: #333333; font-size: 20pt; margin: 0 0 15pt 0; font-weight: bold; }
ul { color: #333333; font-size: 18pt; margin: 0; padding-left: 25pt; }
li { margin-bottom: 12pt; line-height: 1.4; }
</style>
<body>
<div class="header"><h2>セクションタイトル</h2><img class="logo" src="assets/malme-logo.png"></div>
<div class="content">
  <h3>見出し</h3>
  <ul><li>ポイント1</li><li>ポイント2</li></ul>
</div>
</body>
```

---

## 2カラムレイアウト

比較や並列情報の表示用。

```html
<!-- 共通CSS基盤 + 以下 -->
<style>
.content { margin: 20pt 40pt; display: flex; gap: 30pt; }
.column { flex: 1; }
h3 { color: #C2706B; font-size: 20pt; margin: 0 0 15pt 0; font-weight: bold; }
p { font-size: 16pt; margin: 0 0 10pt 0; line-height: 1.4; }
ul { font-size: 16pt; padding-left: 20pt; margin: 0; }
li { margin-bottom: 10pt; line-height: 1.4; }
</style>
<body>
<div class="header"><h2>比較</h2><img class="logo" src="assets/malme-logo.png"></div>
<div class="content">
  <div class="column"><h3>オプションA</h3><p>説明</p></div>
  <div class="column"><h3>オプションB</h3><p>説明</p></div>
</div>
</body>
```

---

## 3カラムレイアウト

3つの並列要素を表示する場合。

```html
<!-- 共通CSS基盤 + 以下 -->
<style>
.content { margin: 20pt 35pt; display: flex; gap: 20pt; }
.column { flex: 1; background: #F5F0F0; padding: 15pt; border-radius: 6pt; }
h3 { color: #C2706B; font-size: 18pt; margin: 0 0 10pt 0; font-weight: bold; }
p { font-size: 14pt; margin: 0; line-height: 1.3; }
</style>
```

---

## データ/チャートスライド

チャートプレースホルダー付きのデータ可視化用。

```html
<!-- 共通CSS基盤 + 以下 -->
<style>
.content { margin: 20pt 35pt; display: flex; gap: 25pt; }
.text-col { width: 35%; }
.chart-col { width: 65%; display: flex; align-items: center; }
h3 { font-size: 18pt; margin: 0 0 12pt 0; }
ul { font-size: 14pt; padding-left: 20pt; }
li { margin-bottom: 8pt; line-height: 1.3; }
.placeholder { background: #F0F0F0; width: 100%; height: 240pt; }
</style>
<div class="chart-col"><div id="chart" class="placeholder"></div></div>
```

---

## 情報密度の高い2カラム

技術レポートや大量情報向け。

```html
<!-- 共通CSS基盤 + 以下 -->
<style>
.header { padding: 10pt 30pt; }
.header h2 { font-size: 20pt; }
.logo { height: 26pt; }
.content { margin: 10pt 30pt; display: flex; gap: 15pt; }
h3 { color: #C2706B; font-size: 12pt; margin: 0 0 6pt 0; }
p { font-size: 9pt; margin: 0 0 4pt 0; line-height: 1.15; }
ul { font-size: 9pt; padding-left: 12pt; }
li { margin-bottom: 3pt; line-height: 1.15; }
table { width: 100%; border-collapse: collapse; font-size: 8pt; margin-bottom: 6pt; }
th { background: #3C3838; color: #FFFFFF; padding: 3pt; text-align: left; }
td { padding: 3pt; border-bottom: 1px solid #E0E0E0; }
.info-box { background: #F5F0F0; padding: 5pt; border-radius: 3pt; margin-bottom: 5pt; }
.highlight-box { background: #F5EAEA; border-left: 2pt solid #C2706B; padding: 5pt; margin-bottom: 5pt; }
</style>
```

---

## テーブルスライド

比較表やデータテーブル用。

```html
<!-- 共通CSS基盤 + 以下 -->
<style>
.header { padding: 12pt 30pt; }
.header h2 { font-size: 22pt; }
.content { margin: 20pt 35pt; }
h3 { font-size: 18pt; margin: 0 0 12pt 0; }
table { width: 100%; border-collapse: collapse; font-size: 14pt; }
th { background: #3C3838; color: #FFFFFF; padding: 8pt 10pt; text-align: left; }
td { padding: 8pt 10pt; border-bottom: 1px solid #E0E0E0; }
tr:nth-child(even) { background: #F5F0F0; }
</style>
<body>
<div class="header"><h2>比較表</h2><img class="logo" src="assets/malme-logo.png"></div>
<div class="content">
  <h3>製品比較</h3>
  <table>
    <tr><th>項目</th><th>製品A</th><th>製品B</th></tr>
    <tr><td>価格</td><td>¥10,000</td><td>¥15,000</td></tr>
    <tr><td>機能</td><td>基本</td><td>拡張</td></tr>
  </table>
</div>
</body>
```

---

## クロージングスライド

背景画像付きの終了スライド。

```html
<style>
body { background-image: url('assets/slide-background.png'); background-size: cover; justify-content: center; align-items: center; }
.logo { position: absolute; top: 20pt; right: 30pt; width: 80pt; }
.content { text-align: center; }
h1 { color: #333333; font-size: 36pt; margin: 0 0 20pt 0; }
p { color: #666666; font-size: 16pt; margin: 0 0 8pt 0; }
p.email { color: #C2706B; }
</style>
<body>
<img class="logo" src="assets/malme-logo.png">
<div class="content">
  <h1>ありがとうございました</h1>
  <p>会社名</p>
  <p class="email">contact@example.com</p>
</div>
</body>
```

---

## オーバーフロー防止ガイド

| 項目 | 標準 | 高密度 |
|-----|------|--------|
| コンテンツマージン | 20-40pt | 10-15pt |
| 見出し(h3) | 18-20pt | 12-14pt |
| 本文/リスト | 14-18pt | 9-11pt |
| 行間 | 1.3-1.4 | 1.15 |
| ボックスpadding | 10-15pt | 5-8pt |
| ボックス間margin | 10-15pt | 4-8pt |

**高密度スライド**: 8項目以上の情報や複雑なテーブルがある場合のみ使用。

---

## レイアウト選択ガイド

| コンテンツ | テンプレート | フォント |
|----------|------------|---------|
| 3-5項目 | コンテンツスライド | 18pt |
| 4-8項目(2列) | 2カラム | 16pt |
| 8項目以上 | 高密度2カラム | 9-11pt |
| 比較表(5行以下) | テーブル | 14pt |
| 比較表(6行以上) | テーブル高密度 | 10-12pt |
