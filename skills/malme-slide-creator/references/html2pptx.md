# HTMLからPowerPointへの変換ガイド

`html2pptx.js` ライブラリを使用して、HTMLスライドを正確な配置でPowerPointプレゼンテーションに変換します。

## 目次

1. [HTMLスライドの作成](#htmlスライドの作成)
2. [html2pptxライブラリの使用](#html2pptxライブラリの使用)
3. [PptxGenJSの使用](#pptxgenjsの使用)

---

## HTMLスライドの作成

すべてのHTMLスライドには適切なボディサイズを含める必要があります:

### レイアウトサイズ

- **16:9** (デフォルト): `width: 720pt; height: 405pt`
- **4:3**: `width: 720pt; height: 540pt`
- **16:10**: `width: 720pt; height: 450pt`

### サポートされる要素

- `<p>`, `<h1>`-`<h6>` - スタイル付きテキスト
- `<ul>`, `<ol>` - リスト (手動の箇条書き記号 •, -, * は使用禁止)
- `<table>`, `<tr>`, `<th>`, `<td>` - テーブル (PowerPointネイティブテーブルに変換)
- `<b>`, `<strong>` - 太字テキスト (インライン書式)
- `<i>`, `<em>` - 斜体テキスト (インライン書式)
- `<u>` - 下線テキスト (インライン書式)
- `<span>` - CSSスタイルでのインライン書式 (太字、斜体、下線、色)
- `<br>` - 改行
- `<div>` (背景/ボーダー付き) - シェイプになる
- `<img>` - 画像
- `class="placeholder"` - チャート用の予約スペース (`{ id, x, y, w, h }` を返す)

### 重要なテキストルール

**すべてのテキストは `<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>` タグの中に配置する必要があります:**
- ✅ 正しい: `<div><p>ここにテキスト</p></div>`
- ❌ 間違い: `<div>ここにテキスト</div>` - **テキストはPowerPointに表示されません**
- ❌ 間違い: `<span>テキスト</span>` - **テキストはPowerPointに表示されません**
- `<div>` や `<span>` 内のテキストタグなしのテキストは無視されます

**手動の箇条書き記号 (•, -, *, など) は絶対に使用しないでください** - 代わりに `<ul>` または `<ol>` リストを使用します

**利用可能なフォント:**
- ✅ 推奨: `'Meiryo'`（日本語プライマリ）, `Arial`（欧文フォールバック）
- ✅ その他利用可能: `Helvetica`, `Times New Roman`, `Georgia`, `Courier New`, `Verdana`, `Tahoma`, `Trebuchet MS`
- ❌ 間違い: `'Segoe UI'`, `'SF Pro'`, `'Roboto'`, カスタムフォント - **レンダリングの問題が発生する可能性があります**

### スタイリング

- マージン崩壊によるオーバーフロー検証の破損を防ぐため、bodyに `display: flex` を使用
- 間隔には `margin` を使用 (paddingはサイズに含まれる)
- インライン書式: `<b>`, `<i>`, `<u>` タグまたは CSSスタイル付きの `<span>` を使用
  - `<span>` がサポートするもの: `font-weight: bold`, `font-style: italic`, `text-decoration: underline`, `color: #rrggbb`
  - `<span>` がサポートしないもの: `margin`, `padding` (PowerPointテキストランでは非対応)
  - 例: `<span style="font-weight: bold; color: #667eea;">太字の青いテキスト</span>`
- Flexboxは動作します - レンダリングされたレイアウトから位置が計算されます
- CSSでは `#` プレフィックス付きの16進数カラーを使用
- **テキスト配置**: テキスト長がわずかにずれる場合のPptxGenJSテキストフォーマットのヒントとして、必要に応じてCSS `text-align` (`center`, `right` など) を使用

### シェイプスタイリング (DIV要素のみ)

**重要: 背景、ボーダー、シャドウは `<div>` 要素にのみ適用され、テキスト要素 (`<p>`, `<h1>`-`<h6>`, `<ul>`, `<ol>`) には適用されません**

- **背景**: `<div>` 要素にのみ CSS `background` または `background-color`
  - 例: `<div style="background: #f0f0f0;">` - 背景付きシェイプを作成
- **ボーダー**: `<div>` 要素の CSS `border` はPowerPointシェイプボーダーに変換
  - 均一ボーダーをサポート: `border: 2px solid #333333`
  - 部分ボーダーをサポート: `border-left`, `border-right`, `border-top`, `border-bottom` (ラインシェイプとしてレンダリング)
  - 例: `<div style="border-left: 8pt solid #E76F51;">`
- **角丸**: 角を丸くするための `<div>` 要素の CSS `border-radius`
  - `border-radius: 50%` 以上で円形シェイプを作成
  - 50%未満のパーセンテージはシェイプの小さい方の寸法に対して計算
  - pxとpt単位をサポート (例: `border-radius: 8pt;`, `border-radius: 12px;`)
  - 例: 100x200pxのボックスで `<div style="border-radius: 25%;">` = 100pxの25% = 25px半径
- **ボックスシャドウ**: `<div>` 要素の CSS `box-shadow` はPowerPointシャドウに変換
  - 外側シャドウのみをサポート (内側シャドウは破損防止のため無視)
  - 例: `<div style="box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);">`
  - 注意: インセット/内側シャドウはPowerPointでサポートされておらず、スキップされます

### テーブルスタイリング

HTMLテーブルはPowerPointネイティブテーブルに自動変換されます:

- **基本構造**: `<table>`, `<tr>`, `<th>`, `<td>` を使用
- **ヘッダー行**: `<th>` 要素は自動的に太字として処理
- **背景色**: CSS `background` または `background-color` でセル背景を設定
  - 例: `th { background: #3C3838; color: #FFFFFF; }`
- **ボーダー**: CSS `border` または `border-bottom` でセルボーダーを設定
  - 例: `td { border-bottom: 1px solid #E0E0E0; }`
- **パディング**: CSS `padding` でセル内余白を設定
- **テキスト配置**: CSS `text-align` で水平配置を設定
- **セル結合**: HTML `colspan` および `rowspan` 属性をサポート

**テーブル例:**
```html
<table>
  <tr>
    <th>項目</th>
    <th>値</th>
  </tr>
  <tr>
    <td>製品A</td>
    <td>¥10,000</td>
  </tr>
  <tr>
    <td>製品B</td>
    <td>¥15,000</td>
  </tr>
</table>
```

**推奨スタイル:**
```css
table { width: 100%; border-collapse: collapse; font-size: 14pt; }
th { background: #3C3838; color: #FFFFFF; padding: 8pt 10pt; text-align: left; }
td { padding: 8pt 10pt; border-bottom: 1px solid #E0E0E0; }
tr:nth-child(even) { background: #F5F0F0; }
```

### アイコンとグラデーション

- **重要: CSSグラデーション (`linear-gradient`, `radial-gradient`) は絶対に使用しないでください** - PowerPointに変換されません
- **常にSharpを使用してグラデーション/アイコンPNGを最初に作成し、HTMLで参照してください**
- グラデーション: SVGをPNG背景画像にラスタライズ
- アイコン: react-icons SVGをPNG画像にラスタライズ
- すべての視覚効果はHTMLレンダリング前にラスター画像として事前レンダリングが必要

**Sharpでアイコンをラスタライズする:**

```javascript
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const sharp = require('sharp');
const { FaHome } = require('react-icons/fa');

async function rasterizeIconPng(IconComponent, color, size = "256", filename) {
  const svgString = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color: `#${color}`, size: size })
  );

  // SharpでSVGをPNGに変換
  await sharp(Buffer.from(svgString))
    .png()
    .toFile(filename);

  return filename;
}

// 使用方法: HTMLで使用する前にアイコンをラスタライズ
const iconPath = await rasterizeIconPng(FaHome, "4472c4", "256", "home-icon.png");
// 次にHTMLで参照: <img src="home-icon.png" style="width: 40pt; height: 40pt;">
```

**Sharpでグラデーションをラスタライズする:**

```javascript
const sharp = require('sharp');

async function createGradientBackground(filename) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="562.5">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:#COLOR1"/>
        <stop offset="100%" style="stop-color:#COLOR2"/>
      </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#g)"/>
  </svg>`;

  await sharp(Buffer.from(svg))
    .png()
    .toFile(filename);

  return filename;
}

// 使用方法: HTML作成前にグラデーション背景を作成
const bgPath = await createGradientBackground("gradient-bg.png");
// 次にHTMLで: <body style="background-image: url('gradient-bg.png');">
```

### 例

```html
<!DOCTYPE html>
<html>
<head>
<style>
html { background: #ffffff; }
body {
  width: 720pt; height: 405pt; margin: 0; padding: 0;
  background: #f5f5f5; font-family: 'Meiryo', Arial, sans-serif;
  display: flex;
}
.content { margin: 30pt; padding: 40pt; background: #ffffff; border-radius: 8pt; }
h1 { color: #2d3748; font-size: 32pt; }
.box {
  background: #70ad47; padding: 20pt; border: 3px solid #5a8f37;
  border-radius: 12pt; box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.25);
}
</style>
</head>
<body>
<div class="content">
  <h1>レシピタイトル</h1>
  <ul>
    <li><b>項目:</b> 説明</li>
  </ul>
  <p><b>太字</b>、<i>斜体</i>、<u>下線</u>のテキスト。</p>
  <div id="chart" class="placeholder" style="width: 350pt; height: 200pt;"></div>

  <!-- テキストは<p>タグ内に配置する必要があります -->
  <div class="box">
    <p>5</p>
  </div>
</div>
</body>
</html>
```

## html2pptxライブラリの使用

### 依存関係

以下のライブラリはグローバルにインストールされており、使用可能です:
- `pptxgenjs`
- `playwright`
- `sharp`

### 基本的な使用方法

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_16x9';  // HTMLボディサイズと一致させる必要があります

const { slide, placeholders } = await html2pptx('slide1.html', pptx);

// プレースホルダーエリアにチャートを追加
if (placeholders.length > 0) {
    slide.addChart(pptx.charts.LINE, chartData, placeholders[0]);
}

await pptx.writeFile('output.pptx');
```

### APIリファレンス

#### 関数シグネチャ
```javascript
await html2pptx(htmlFile, pres, options)
```

#### パラメータ
- `htmlFile` (string): HTMLファイルへのパス (絶対または相対)
- `pres` (pptxgen): レイアウトが設定済みのPptxGenJSプレゼンテーションインスタンス
- `options` (object, オプション):
  - `tmpDir` (string): 生成ファイル用の一時ディレクトリ (デフォルト: `process.env.TMPDIR || '/tmp'`)
  - `slide` (object): 再利用する既存スライド (デフォルト: 新しいスライドを作成)

#### 戻り値
```javascript
{
    slide: pptxgenSlide,           // 作成/更新されたスライド
    placeholders: [                 // プレースホルダー位置の配列
        { id: string, x: number, y: number, w: number, h: number },
        ...
    ]
}
```

### バリデーション

ライブラリは自動的に検証し、スロー前にすべてのエラーを収集します:

1. **HTMLサイズはプレゼンテーションレイアウトと一致する必要がある** - サイズの不一致を報告
2. **コンテンツがボディからオーバーフローしてはならない** - 正確な測定値でオーバーフローを報告
3. **CSSグラデーション** - サポートされていないグラデーションの使用を報告
4. **テキスト要素のスタイリング** - テキスト要素への背景/ボーダー/シャドウを報告 (divにのみ許可)

**すべてのバリデーションエラーは収集され、単一のエラーメッセージにまとめて報告されます。** これにより、一度に一つずつではなく、すべての問題を一度に修正できます。

### プレースホルダーの操作

```javascript
const { slide, placeholders } = await html2pptx('slide.html', pptx);

// 最初のプレースホルダーを使用
slide.addChart(pptx.charts.BAR, data, placeholders[0]);

// IDで検索
const chartArea = placeholders.find(p => p.id === 'chart-area');
slide.addChart(pptx.charts.LINE, data, chartArea);
```

### 完全な例

```javascript
const pptxgen = require('pptxgenjs');
const html2pptx = require('./html2pptx');

async function createPresentation() {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';
    pptx.author = 'あなたの名前';
    pptx.title = '私のプレゼンテーション';

    // スライド1: タイトル
    const { slide: slide1 } = await html2pptx('slides/title.html', pptx);

    // スライド2: チャート付きコンテンツ
    const { slide: slide2, placeholders } = await html2pptx('slides/data.html', pptx);

    const chartData = [{
        name: '売上',
        labels: ['Q1', 'Q2', 'Q3', 'Q4'],
        values: [4500, 5500, 6200, 7100]
    }];

    slide2.addChart(pptx.charts.BAR, chartData, {
        ...placeholders[0],
        showTitle: true,
        title: '四半期売上',
        showCatAxisTitle: true,
        catAxisTitle: '四半期',
        showValAxisTitle: true,
        valAxisTitle: '売上 (千ドル)'
    });

    // 保存
    await pptx.writeFile({ fileName: 'presentation.pptx' });
    console.log('プレゼンテーションが正常に作成されました!');
}

createPresentation().catch(console.error);
```

## PptxGenJSの使用

`html2pptx` でHTMLをスライドに変換した後、PptxGenJSを使用してチャート、画像、追加要素などの動的コンテンツを追加します。

### ⚠️ 重要なルール

#### カラー
- PptxGenJSで16進数カラーに **`#` プレフィックスを絶対に使用しない** - ファイル破損の原因になります
- ✅ 正しい: `color: "FF0000"`, `fill: { color: "0066CC" }`
- ❌ 間違い: `color: "#FF0000"` (ドキュメントが壊れる)

### 画像の追加

常に実際の画像サイズからアスペクト比を計算します:

```javascript
// 画像サイズを取得: identify image.png | grep -o '[0-9]* x [0-9]*'
const imgWidth = 1860, imgHeight = 1519;  // 実際のファイルから
const aspectRatio = imgWidth / imgHeight;

const h = 3;  // 最大高さ
const w = h * aspectRatio;
const x = (10 - w) / 2;  // 16:9スライドで中央揃え

slide.addImage({ path: "chart.png", x, y: 1.5, w, h });
```

### テキストの追加

```javascript
// 書式付きリッチテキスト
slide.addText([
    { text: "太字 ", options: { bold: true } },
    { text: "斜体 ", options: { italic: true } },
    { text: "通常" }
], {
    x: 1, y: 2, w: 8, h: 1
});
```

### シェイプの追加

```javascript
// 四角形
slide.addShape(pptx.shapes.RECTANGLE, {
    x: 1, y: 1, w: 3, h: 2,
    fill: { color: "4472C4" },
    line: { color: "000000", width: 2 }
});

// 円
slide.addShape(pptx.shapes.OVAL, {
    x: 5, y: 1, w: 2, h: 2,
    fill: { color: "ED7D31" }
});

// 角丸四角形
slide.addShape(pptx.shapes.ROUNDED_RECTANGLE, {
    x: 1, y: 4, w: 3, h: 1.5,
    fill: { color: "70AD47" },
    rectRadius: 0.2
});
```

### チャートの追加

**ほとんどのチャートに必須:** `catAxisTitle` (カテゴリ) と `valAxisTitle` (値) を使用した軸ラベル。

**チャートデータ形式:**
- 単純な棒/折れ線グラフには **すべてのラベルを含む単一シリーズ** を使用
- 各シリーズは個別の凡例エントリを作成
- ラベル配列はX軸の値を定義

**時系列データ - 正しい粒度を選択:**
- **30日未満**: 日次グループ化を使用 (例: "10-01", "10-02") - 単一ポイントのチャートを作成する月次集計は避ける
- **30-365日**: 月次グループ化を使用 (例: "2024-01", "2024-02")
- **365日超**: 年次グループ化を使用 (例: "2023", "2024")
- **検証**: データポイントが1つだけのチャートは、期間に対して不正な集計を示している可能性が高い

```javascript
const { slide, placeholders } = await html2pptx('slide.html', pptx);

// 正しい: すべてのラベルを含む単一シリーズ
slide.addChart(pptx.charts.BAR, [{
    name: "2024年売上",
    labels: ["Q1", "Q2", "Q3", "Q4"],
    values: [4500, 5500, 6200, 7100]
}], {
    ...placeholders[0],  // プレースホルダー位置を使用
    barDir: 'col',       // 'col' = 縦棒、'bar' = 横棒
    showTitle: true,
    title: '四半期売上',
    showLegend: false,   // 単一シリーズでは凡例不要
    // 必須の軸ラベル
    showCatAxisTitle: true,
    catAxisTitle: '四半期',
    showValAxisTitle: true,
    valAxisTitle: '売上 (千ドル)',
    // オプション: スケーリング制御 (より良い視覚化のためにデータ範囲に基づいて最小値を調整)
    valAxisMaxVal: 8000,
    valAxisMinVal: 0,  // カウント/金額には0を使用; クラスタ化されたデータ (例: 4500-7100) には、最小値に近い値から開始することを検討
    valAxisMajorUnit: 2000,  // 混雑を防ぐためにY軸ラベル間隔を制御
    catAxisLabelRotate: 45,  // 混雑している場合はラベルを回転
    dataLabelPosition: 'outEnd',
    dataLabelColor: '000000',
    // 単一シリーズチャートには単一色を使用
    chartColors: ["4472C4"]  // すべての棒が同じ色
});
```

#### 散布図

**重要**: 散布図のデータ形式は特殊です - 最初のシリーズにX軸の値、後続のシリーズにY値が含まれます:

```javascript
// データを準備
const data1 = [{ x: 10, y: 20 }, { x: 15, y: 25 }, { x: 20, y: 30 }];
const data2 = [{ x: 12, y: 18 }, { x: 18, y: 22 }];

const allXValues = [...data1.map(d => d.x), ...data2.map(d => d.x)];

slide.addChart(pptx.charts.SCATTER, [
    { name: 'X軸', values: allXValues },  // 最初のシリーズ = X値
    { name: 'シリーズ1', values: data1.map(d => d.y) },  // Y値のみ
    { name: 'シリーズ2', values: data2.map(d => d.y) }   // Y値のみ
], {
    x: 1, y: 1, w: 8, h: 4,
    lineSize: 0,  // 0 = 接続線なし
    lineDataSymbol: 'circle',
    lineDataSymbolSize: 6,
    showCatAxisTitle: true,
    catAxisTitle: 'X軸',
    showValAxisTitle: true,
    valAxisTitle: 'Y軸',
    chartColors: ["4472C4", "ED7D31"]
});
```

#### 折れ線グラフ

```javascript
slide.addChart(pptx.charts.LINE, [{
    name: "気温",
    labels: ["1月", "2月", "3月", "4月"],
    values: [32, 35, 42, 55]
}], {
    x: 1, y: 1, w: 8, h: 4,
    lineSize: 4,
    lineSmooth: true,
    // 必須の軸ラベル
    showCatAxisTitle: true,
    catAxisTitle: '月',
    showValAxisTitle: true,
    valAxisTitle: '気温 (°F)',
    // オプション: Y軸範囲 (より良い視覚化のためにデータ範囲に基づいて最小値を設定)
    valAxisMinVal: 0,     // 0から始まる範囲 (カウント、パーセンテージなど)
    valAxisMaxVal: 60,
    valAxisMajorUnit: 20,  // 混雑を防ぐためにY軸ラベル間隔を制御 (例: 10, 20, 25)
    // valAxisMinVal: 30,  // 推奨: 範囲内にクラスタ化されたデータ (例: 32-55 や 3-5の評価) には、変化を示すために最小値に近い軸開始
    // オプション: チャート色
    chartColors: ["4472C4", "ED7D31", "A5A5A5"]
});
```

#### 円グラフ (軸ラベル不要)

**重要**: 円グラフには `labels` 配列にすべてのカテゴリ、`values` 配列に対応する値を持つ **単一データシリーズ** が必要です。

```javascript
slide.addChart(pptx.charts.PIE, [{
    name: "市場シェア",
    labels: ["製品A", "製品B", "その他"],  // すべてのカテゴリを1つの配列に
    values: [35, 45, 20]  // すべての値を1つの配列に
}], {
    x: 2, y: 1, w: 6, h: 4,
    showPercent: true,
    showLegend: true,
    legendPos: 'r',  // 右
    chartColors: ["4472C4", "ED7D31", "A5A5A5"]
});
```

#### 複数データシリーズ

```javascript
slide.addChart(pptx.charts.LINE, [
    {
        name: "製品A",
        labels: ["Q1", "Q2", "Q3", "Q4"],
        values: [10, 20, 30, 40]
    },
    {
        name: "製品B",
        labels: ["Q1", "Q2", "Q3", "Q4"],
        values: [15, 25, 20, 35]
    }
], {
    x: 1, y: 1, w: 8, h: 4,
    showCatAxisTitle: true,
    catAxisTitle: '四半期',
    showValAxisTitle: true,
    valAxisTitle: '売上 (百万ドル)'
});
```

### チャートカラー

**重要**: `#` プレフィックス **なし** の16進数カラーを使用 - `#` を含めるとファイルが破損します。

**チャートカラーは選択したデザインパレットに合わせて**、データ視覚化のための十分なコントラストと識別性を確保してください。以下の点で色を調整:
- 隣接するシリーズ間の強いコントラスト
- スライド背景に対する可読性
- アクセシビリティ (赤緑のみの組み合わせは避ける)

```javascript
// 例: オーシャンパレットにインスパイアされたチャートカラー (コントラスト調整済み)
const chartColors = ["16A085", "FF6B9D", "2C3E50", "F39C12", "9B59B6"];

// 単一シリーズチャート: すべての棒/ポイントに1色を使用
slide.addChart(pptx.charts.BAR, [{
    name: "売上",
    labels: ["Q1", "Q2", "Q3", "Q4"],
    values: [4500, 5500, 6200, 7100]
}], {
    ...placeholders[0],
    chartColors: ["16A085"],  // すべての棒が同じ色
    showLegend: false
});

// 複数シリーズチャート: 各シリーズに異なる色
slide.addChart(pptx.charts.LINE, [
    { name: "製品A", labels: ["Q1", "Q2", "Q3"], values: [10, 20, 30] },
    { name: "製品B", labels: ["Q1", "Q2", "Q3"], values: [15, 25, 20] }
], {
    ...placeholders[0],
    chartColors: ["16A085", "FF6B9D"]  // シリーズごとに1色
});
```

### テーブルの追加

テーブルは基本的または高度な書式設定で追加できます:

#### 基本テーブル

```javascript
slide.addTable([
    ["ヘッダー1", "ヘッダー2", "ヘッダー3"],
    ["行1, 列1", "行1, 列2", "行1, 列3"],
    ["行2, 列1", "行2, 列2", "行2, 列3"]
], {
    x: 0.5,
    y: 1,
    w: 9,
    h: 3,
    border: { pt: 1, color: "999999" },
    fill: { color: "F1F1F1" }
});
```

#### カスタム書式設定付きテーブル

```javascript
const tableData = [
    // カスタムスタイル付きヘッダー行
    [
        { text: "製品", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } },
        { text: "売上", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } },
        { text: "成長率", options: { fill: { color: "4472C4" }, color: "FFFFFF", bold: true } }
    ],
    // データ行
    ["製品A", "$50M", "+15%"],
    ["製品B", "$35M", "+22%"],
    ["製品C", "$28M", "+8%"]
];

slide.addTable(tableData, {
    x: 1,
    y: 1.5,
    w: 8,
    h: 3,
    colW: [3, 2.5, 2.5],  // 列幅
    rowH: [0.5, 0.6, 0.6, 0.6],  // 行高さ
    border: { pt: 1, color: "CCCCCC" },
    align: "center",
    valign: "middle",
    fontSize: 14
});
```

#### セル結合付きテーブル

```javascript
const mergedTableData = [
    [
        { text: "Q1結果", options: { colspan: 3, fill: { color: "4472C4" }, color: "FFFFFF", bold: true } }
    ],
    ["製品", "売上", "市場シェア"],
    ["製品A", "$25M", "35%"],
    ["製品B", "$18M", "25%"]
];

slide.addTable(mergedTableData, {
    x: 1,
    y: 1,
    w: 8,
    h: 2.5,
    colW: [3, 2.5, 2.5],
    border: { pt: 1, color: "DDDDDD" }
});
```

### テーブルオプション

一般的なテーブルオプション:
- `x, y, w, h` - 位置とサイズ
- `colW` - 列幅の配列 (インチ)
- `rowH` - 行高さの配列 (インチ)
- `border` - ボーダースタイル: `{ pt: 1, color: "999999" }`
- `fill` - 背景色 (#プレフィックスなし)
- `align` - テキスト配置: "left", "center", "right"
- `valign` - 垂直配置: "top", "middle", "bottom"
- `fontSize` - テキストサイズ
- `autoPage` - コンテンツがオーバーフローした場合に新しいスライドを自動作成
