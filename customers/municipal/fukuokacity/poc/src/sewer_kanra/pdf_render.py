"""PDFページのレンダリングと bbox オーバーレイ描画。

Gemini Vision が返した `source = {page, bbox}` を可視化するためのヘルパー。

座標規約:
- ページ番号: **1-indexed**
- bbox: `[ymin, xmin, ymax, xmax]` の4要素、0-1000 に正規化（Gemini spatial understanding 慣例）
- 左上が (0, 0)、右下が (1000, 1000)
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pdfplumber
from PIL import Image, ImageDraw, ImageFont


# ---------- レンダリング ----------
def render_page(pdf_path: Path, page_idx_1based: int, dpi: int = 144) -> Image.Image:
    """PDF の指定ページを PIL Image にレンダリングする。"""
    if page_idx_1based < 1:
        raise ValueError(f"page_idx_1based must be >= 1, got {page_idx_1based}")
    with pdfplumber.open(str(pdf_path)) as pdf:
        if page_idx_1based > len(pdf.pages):
            raise ValueError(
                f"page index out of range: {page_idx_1based} > {len(pdf.pages)}"
            )
        page = pdf.pages[page_idx_1based - 1]
        return page.to_image(resolution=dpi).original.convert("RGB")


# ---------- 座標変換 ----------
def denormalize_bbox(
    bbox_0_1000: Sequence[float], width: int, height: int
) -> tuple[int, int, int, int]:
    """[ymin, xmin, ymax, xmax] (0-1000) → (x0, y0, x1, y1) ピクセル座標。

    Gemini Vision の bbox 慣例（[ymin, xmin, ymax, xmax]）→ Pillow の (x0, y0, x1, y1)。
    """
    ymin, xmin, ymax, xmax = bbox_0_1000
    x0 = int(xmin / 1000.0 * width)
    y0 = int(ymin / 1000.0 * height)
    x1 = int(xmax / 1000.0 * width)
    y1 = int(ymax / 1000.0 * height)
    # 軽い正規化（順序逆転や範囲外を救済）
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    x0 = max(0, min(x0, width - 1))
    y0 = max(0, min(y0, height - 1))
    x1 = max(0, min(x1, width))
    y1 = max(0, min(y1, height))
    return x0, y0, x1, y1


# ---------- フォント ----------
_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",  # macOS
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
    "/Library/Fonts/Arial.ttf",
]


def _load_font(size: int) -> ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


# ---------- オーバーレイ ----------
def overlay_numbered_boxes(
    image: Image.Image,
    items: Iterable[dict],
    color: tuple[int, int, int] = (220, 38, 38),  # red-600
) -> Image.Image:
    """画像の上に番号付き矩形を描画して新しい画像を返す。

    items の各要素は `{"index": int, "bbox_px": (x0, y0, x1, y1), "label": str}`。
    `bbox_px` は既にピクセル座標化済みであることを期待する（denormalize_bbox の戻り値）。
    """
    img = image.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    width, height = img.size
    line_w = max(2, int(min(width, height) / 500))
    font_size = max(14, int(min(width, height) / 60))
    font = _load_font(font_size)
    label_bg = (*color, 230)
    label_fg = (255, 255, 255, 255)
    box_outline = (*color, 255)
    box_fill = (*color, 40)

    for it in items:
        x0, y0, x1, y1 = it["bbox_px"]
        if x1 <= x0 or y1 <= y0:
            continue
        # 半透明塗り + 太線
        draw.rectangle([x0, y0, x1, y1], fill=box_fill, outline=box_outline, width=line_w)
        # 番号ラベル（左上に貼る）
        label = it.get("label", str(it.get("index", "?")))
        try:
            tx0, ty0, tx1, ty1 = draw.textbbox((0, 0), label, font=font)
            tw, th = tx1 - tx0, ty1 - ty0
        except AttributeError:
            tw, th = font.getsize(label)  # Pillow <10 fallback
        pad = max(2, int(font_size * 0.2))
        lx0 = max(0, x0)
        ly0 = max(0, y0 - th - 2 * pad)
        if ly0 < 0:
            ly0 = y0  # 上にはみ出すなら矩形内に
        draw.rectangle(
            [lx0, ly0, lx0 + tw + 2 * pad, ly0 + th + 2 * pad],
            fill=label_bg,
        )
        draw.text((lx0 + pad, ly0 + pad), label, fill=label_fg, font=font)

    return img


# ---------- ペイロード→ページ別オーバーレイ ----------
def build_overlay_for_payload(
    pdf_path: Path,
    items_with_source: Sequence[dict],
    label_field: str = "value",
    dpi: int = 144,
) -> dict[int, Image.Image]:
    """payload の項目から、ページ別のオーバーレイ画像 dict を返す。

    Args:
        pdf_path: PDF ファイル
        items_with_source: 各要素に `source.page` `source.bbox` を持つ可能性がある dict のリスト。
            元配列の index がそのまま「番号」になる（1-indexed で表示）
        label_field: 番号と一緒に小さく表示したいフィールド名（未使用、将来拡張）

    Returns:
        {page_idx_1based: PIL.Image} の dict。bbox を持つ項目があるページのみ含まれる。
    """
    # ページごとに項目をまとめる
    per_page: dict[int, list[dict]] = {}
    for i, item in enumerate(items_with_source, start=1):  # 1-indexed
        src = item.get("source") or {}
        page = src.get("page")
        bbox = src.get("bbox")
        if not isinstance(page, int) or not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        per_page.setdefault(page, []).append(
            {"index": i, "bbox_norm": bbox, "label": str(i)}
        )

    if not per_page:
        return {}

    out: dict[int, Image.Image] = {}
    with pdfplumber.open(str(pdf_path)) as pdf:
        n_pages = len(pdf.pages)
        for page_idx, raw_items in per_page.items():
            if page_idx < 1 or page_idx > n_pages:
                continue
            page = pdf.pages[page_idx - 1]
            img = page.to_image(resolution=dpi).original.convert("RGB")
            w, h = img.size
            ready = []
            for it in raw_items:
                bp = denormalize_bbox(it["bbox_norm"], w, h)
                ready.append({"index": it["index"], "bbox_px": bp, "label": it["label"]})
            out[page_idx] = overlay_numbered_boxes(img, ready)
    return out


def count_with_source(items_with_source: Sequence[dict]) -> tuple[int, int]:
    """source 情報を持つ項目の数 / 全項目数 を返す。"""
    total = len(items_with_source)
    have = 0
    for item in items_with_source:
        src = item.get("source") or {}
        if isinstance(src.get("page"), int) and isinstance(src.get("bbox"), (list, tuple)):
            have += 1
    return have, total


# ---------- 単独実行（動作確認用） ----------
def _smoke_test() -> int:
    """case_001 の図面PDFをレンダーして、ダミー bbox を重ね描きする。"""
    import sys

    from . import paths

    pdf = paths.case_drawing_pdf("case_001")
    if pdf is None or not pdf.exists():
        print(f"PDF not found for case_001: {pdf}", file=sys.stderr)
        return 1

    dummy_items = [
        {"value": "18.10", "source": {"page": 1, "bbox": [200, 100, 250, 220]}},
        {"value": "TPφ250", "source": {"page": 1, "bbox": [400, 300, 450, 460]}},
        {"value": "i=11.2", "source": {"page": 1, "bbox": [600, 500, 650, 620]}},
    ]
    out = build_overlay_for_payload(pdf, dummy_items)
    if not out:
        print("No overlay generated (no bbox found?)", file=sys.stderr)
        return 1
    out_dir = pdf.parent / "_pdf_render_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)
    for page_idx, img in out.items():
        target = out_dir / f"page_{page_idx}.png"
        img.save(target)
        print(f"Wrote {target} ({img.size[0]}x{img.size[1]})")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(_smoke_test())
