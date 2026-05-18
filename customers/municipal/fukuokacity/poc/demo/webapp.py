"""福岡市 PoC デモ Webビューア（Streamlit）

起動:
    cd customers/municipal/fukuokacity/poc
    streamlit run demo/webapp.py

機能:
    - ケース選択（case_001..006）と PDF プレビュー
    - パイプライン実行（extract-calc / extract-drawing / consistency / eval）
    - 数量計算書ドラフトの DataFrame 表示
    - 数量総括表（L2-L3-L4 階層）の表示
    - 整合性チェック結果と精度メトリクスの可視化
    - 川畑さん/福岡市同時提示用の説明テキスト
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# src/ を import path に追加
DEMO_DIR = Path(__file__).resolve().parent
POC_ROOT = DEMO_DIR.parent
SRC = POC_ROOT / "src"
sys.path.insert(0, str(SRC))

from sewer_kanra import paths  # noqa: E402

st.set_page_config(
    page_title="下水道数量計算書 自動生成 PoC",
    page_icon="🚇",
    layout="wide",
)

st.title("🚇 下水道工事 図面→数量計算書 自動生成 PoC")
st.caption("福岡市道路下水道局 / 那珂二丁目外地区下水道築造工事 をサンプルケースに")

# ---------- サイドバー ----------
with st.sidebar:
    st.header("⚙️ 設定")
    case_options = [c for c, _ in paths.CASES]
    case_id = st.selectbox(
        "ケース選択",
        case_options,
        format_func=lambda c: f"{c}（路線 {dict(paths.CASES)[c]}）",
    )
    route = dict(paths.CASES)[case_id]

    st.divider()
    st.subheader("⚡ パイプライン実行")
    st.caption("`GEMINI_API_KEY` が必要")
    run_calc = st.button("📄 計算書抽出（Gemini）")
    run_drawing = st.button("🖼 図面抽出（Gemini）")
    run_check = st.button("🔍 整合性チェック")
    run_eval = st.button("📊 GT 評価（F1）")
    run_all = st.button("🚀 一括実行（all）", type="primary")

    st.divider()
    st.subheader("🧭 製品方針")
    st.caption("2026-05-08 方針確定")
    st.markdown(
        "- **自治体スキーマを持たない**\n"
        "- 図面PDF → Vision LLM で **汎用抽出**\n"
        "- 中間表現は **JS共通工種体系**\n"
        "- 自治体差は **出力フォーマッタ** で吸収\n"
        "  - 福岡市: `schema/fukuoka_soukatu.yaml`\n"
        "- **DWG非対応**（PoCはPDF限定）"
    )

    st.divider()
    st.subheader("📁 上位文書")
    st.markdown(
        "- [計画ファイル](swift-hatching-comet.md)\n"
        "- [事業性評価](../../feasibility_quantity_calc_2026-05-07.md)\n"
        "- [パターン分析](../../../comparison/_pattern_analysis.md)"
    )


# ---------- メイン ----------
def show_pdf_preview(label: str, pdf_path: Path | None) -> None:
    if pdf_path is None or not pdf_path.exists():
        st.info(f"{label}: 該当PDFなし")
        return
    st.caption(f"{label}: `{pdf_path.relative_to(POC_ROOT)}`")
    try:
        with open(pdf_path, "rb") as f:
            data = f.read()
        st.download_button(
            f"📥 {label}をダウンロード",
            data,
            file_name=pdf_path.name,
            mime="application/pdf",
        )
    except Exception as e:
        st.warning(f"{label} 読み込み失敗: {e}")


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception as e:
        st.error(f"JSON parse failed: {path.name}: {e}")
        return None


# ---------- 検出位置オーバーレイ ----------
def _indexed_dataframe(items: list[dict]) -> pd.DataFrame:
    """先頭に # 列（1-indexed）を持つ DataFrame を返す。番号はオーバーレイ画像と一致する。"""
    df = pd.DataFrame(items)
    if not df.empty:
        df.insert(0, "#", range(1, len(df) + 1))
    return df


@st.cache_data(show_spinner=False, max_entries=20)
def _render_overlay_pngs(pdf_bytes: bytes, items_json: str) -> dict[int, bytes]:
    """PDFバイトと items の JSON 文字列から、ページ別オーバーレイPNGバイトの辞書を生成。"""
    import io

    from sewer_kanra.pdf_render import build_overlay_for_payload

    items = json.loads(items_json)
    with tempfile.TemporaryDirectory() as td:
        pdf_path = Path(td) / "src.pdf"
        pdf_path.write_bytes(pdf_bytes)
        overlays = build_overlay_for_payload(pdf_path, items)
        out: dict[int, bytes] = {}
        for p, img in overlays.items():
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            out[p] = buf.getvalue()
    return out


def _render_overlay_section(pdf_bytes: bytes | None, items: list[dict], label: str) -> None:
    """検出位置オーバーレイを描画する共通関数。"""
    from sewer_kanra.pdf_render import count_with_source

    if not items:
        return
    have, total = count_with_source(items)
    if pdf_bytes is None:
        st.info(f"📍 {label}: PDFデータが見つからずレンダリングできません（出典情報 {have}/{total} 件）")
        return
    if total == 0:
        return
    if have == 0:
        st.info(
            f"📍 {label}: 出典情報あり 0 / {total} 件 — "
            "Vision LLM が source を返していません（古い結果か、認識失敗）"
        )
        return
    st.caption(f"📍 {label}: 出典情報あり **{have} / {total}** 件（番号は表の `#` 列と対応）")
    items_json = json.dumps(items, ensure_ascii=False, sort_keys=True)
    try:
        overlays = _render_overlay_pngs(pdf_bytes, items_json)
    except Exception as e:
        st.error(f"レンダリング失敗: {e}")
        return
    if not overlays:
        st.info("有効な bbox が見つかりませんでした")
        return
    page_keys = sorted(overlays.keys())
    if len(page_keys) > 1:
        page_tabs = st.tabs([f"Page {p}" for p in page_keys])
        for sub, p in zip(page_tabs, page_keys):
            with sub:
                st.image(overlays[p], use_container_width=True)
    else:
        p = page_keys[0]
        st.image(overlays[p], caption=f"Page {p}", use_container_width=True)


def _read_pdf_bytes(path: Path | None) -> bytes | None:
    if path is None or not path.exists():
        return None
    try:
        return path.read_bytes()
    except Exception:
        return None


# ---------- パイプライン実行 ----------
def _run_subcommand(name: str, case: str | None = None) -> None:
    """sewer_kanra CLI を Python 内呼び出し"""
    import argparse
    from sewer_kanra import cli  # noqa: E402

    args = argparse.Namespace(case=case)
    func = {
        "extract-calc": cli.cmd_extract_calc,
        "extract-drawing": cli.cmd_extract_drawing,
        "check": cli.cmd_check,
        "eval": cli.cmd_eval,
        "aggregate": cli.cmd_aggregate,
        "all": cli.cmd_all,
    }[name]
    with st.status(f"🛠️ {name} を実行中（{case or '全件'}）...", expanded=True) as status:
        try:
            rc = func(args)
            status.update(label=f"✅ {name} 完了 (rc={rc})", state="complete")
        except Exception as e:
            st.exception(e)
            status.update(label=f"❌ {name} 失敗: {e}", state="error")


if run_calc:
    _run_subcommand("extract-calc", case=case_id)
if run_drawing:
    _run_subcommand("extract-drawing", case=case_id)
if run_check:
    _run_subcommand("check", case=case_id)
if run_eval:
    _run_subcommand("eval", case=case_id)
if run_all:
    _run_subcommand("all", case=case_id)


# ---------- タブ ----------
tab_upload, tab_overview, tab_calc, tab_soukatu, tab_check, tab_eval = st.tabs(
    ["📤 アップロード解析", "概要", "数量計算書ドラフト", "数量総括表", "整合性レポート", "精度メトリクス"]
)


# ---------- アップロード解析タブ ----------
def _run_upload_analysis(
    drawing_bytes: bytes,
    drawing_name: str,
    calc_bytes: bytes | None,
    calc_name: str | None,
    route: str,
) -> dict:
    """アップロードされたPDFを一時ファイルに書き出し、Gemini Vision で抽出する。

    返り値: {drawing, calc, consistency} — calc/consistency は計算書アップロード時のみ
    """
    from sewer_kanra import extract_calc_book, extract_drawing, consistency_check  # noqa: E402
    from sewer_kanra.gemini_client import GeminiClient  # noqa: E402

    knowledge = paths.KNOWLEDGE_FILE.read_text()
    client = GeminiClient()
    out: dict = {"drawing": None, "calc": None, "consistency": None}

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        drawing_path = td_path / drawing_name
        drawing_path.write_bytes(drawing_bytes)
        out["drawing"] = extract_drawing.extract(
            drawing_path, expected_route=route, knowledge=knowledge, client=client
        )

        if calc_bytes is not None and calc_name is not None:
            calc_path = td_path / calc_name
            calc_path.write_bytes(calc_bytes)
            out["calc"] = extract_calc_book.extract(
                calc_path, expected_route=route, knowledge=knowledge, client=client
            )
            out["consistency"] = consistency_check.check_payloads(
                out["calc"], out["drawing"], case_id="upload", route=route
            )

    return out


with tab_upload:
    st.subheader("📤 図面アップロード → 数量抽出")
    st.caption(
        "図面PDFを投入すると Gemini Vision で工種・規格・数量を直接抽出します"
        "（汎用抽出ロジック／自治体スキーマなし）"
    )

    if not os.environ.get("GEMINI_API_KEY"):
        st.error("`GEMINI_API_KEY` が未設定です。`.env` を設定してから再実行してください。")

    col_form, col_help = st.columns([2, 1])
    with col_form:
        up_drawing = st.file_uploader(
            "📐 図面PDF（必須）",
            type=["pdf"],
            key="upload_drawing_file",
        )
        up_calc = st.file_uploader(
            "📄 数量計算書PDF（任意）",
            type=["pdf"],
            key="upload_calc_file",
            help="アップロードすると整合性チェック（図面 vs 計算書）も実行します",
        )
        up_route = st.text_input(
            "🛤 路線番号（必須）",
            value="",
            placeholder="例: 429-2",
            key="upload_route_input",
            help="図面に書かれている路線番号を入力。半角ハイフン区切り",
        )
        run_disabled = (up_drawing is None) or (not up_route.strip()) or (
            not os.environ.get("GEMINI_API_KEY")
        )
        run_upload = st.button(
            "🔍 解析実行",
            type="primary",
            disabled=run_disabled,
            key="upload_run_button",
        )

    with col_help:
        st.info(
            "**入力**\n"
            "- 図面PDF（必須）\n"
            "- 計算書PDF（任意）\n"
            "- 路線番号（必須）\n\n"
            "**処理**\n"
            "- Gemini Vision で抽出\n"
            "- セッション内のみ保持（保存なし）\n\n"
            "**目安所要時間**\n"
            "- 図面のみ ~10s\n"
            "- 図面+計算書 ~25s"
        )

    if run_upload:
        with st.status("🛠️ Gemini Vision で抽出中…", expanded=True) as status:
            try:
                result = _run_upload_analysis(
                    drawing_bytes=up_drawing.getvalue(),
                    drawing_name=up_drawing.name,
                    calc_bytes=up_calc.getvalue() if up_calc is not None else None,
                    calc_name=up_calc.name if up_calc is not None else None,
                    route=up_route.strip(),
                )
                st.session_state["upload_result"] = result
                st.session_state["upload_route_used"] = up_route.strip()
                st.session_state["upload_drawing_filename"] = up_drawing.name
                st.session_state["upload_calc_filename"] = (
                    up_calc.name if up_calc is not None else None
                )
                st.session_state["upload_drawing_bytes"] = up_drawing.getvalue()
                st.session_state["upload_calc_bytes"] = (
                    up_calc.getvalue() if up_calc is not None else None
                )
                status.update(label="✅ 抽出完了", state="complete")
            except Exception as e:
                st.exception(e)
                status.update(label=f"❌ 失敗: {e}", state="error")

    # ---------- 結果表示（セッションに残っていれば） ----------
    result = st.session_state.get("upload_result")
    if result is None:
        st.info("図面PDFと路線番号を入力して『解析実行』を押してください。")
    else:
        used_route = st.session_state.get("upload_route_used", "?")
        used_drawing = st.session_state.get("upload_drawing_filename", "?")
        used_calc = st.session_state.get("upload_calc_filename")
        st.markdown(
            f"#### 解析結果  `路線 {used_route}`  ／  図面: `{used_drawing}`"
            + (f"  ／  計算書: `{used_calc}`" if used_calc else "  （計算書なし）")
        )

        sub_t1, sub_t2, sub_t3, sub_t4 = st.tabs(
            ["🖼 図面抽出", "📄 計算書ドラフト", "🔍 整合性", "🔧 生JSON"]
        )

        # --- 図面抽出 ---
        with sub_t1:
            d = result.get("drawing") or {}
            meta = d.get("_meta", {})
            col1, col2, col3 = st.columns(3)
            col1.metric("検出値数", len(d.get("detected_values", [])))
            col2.metric("マンホール", len(d.get("manholes", [])))
            col3.metric("既設埋設物", len(d.get("buried_utilities", [])))
            st.caption(
                f"路線（推定）: `{d.get('route', '?')}`  /  "
                f"図面種別: `{d.get('drawing_type', '?')}`  /  "
                f"縮尺: `{d.get('scale', '?')}`  /  "
                f"モデル: `{meta.get('model', '?')}`  /  "
                f"所要: {meta.get('elapsed_s', '?')}s"
            )
            dv = d.get("detected_values", [])
            if dv:
                st.markdown("##### detected_values")
                st.dataframe(_indexed_dataframe(dv), use_container_width=True, height=350)
            else:
                st.warning("detected_values が空でした。")
            mh = d.get("manholes", [])
            if mh:
                with st.expander("🕳 マンホール"):
                    st.dataframe(pd.DataFrame(mh), use_container_width=True)
            bu = d.get("buried_utilities", [])
            if bu:
                with st.expander("🚧 既設埋設物"):
                    st.dataframe(pd.DataFrame(bu), use_container_width=True)

            # 検出位置オーバーレイ
            if dv:
                with st.expander("📍 検出位置（PDFのどこから読んだか）", expanded=False):
                    _render_overlay_section(
                        st.session_state.get("upload_drawing_bytes"),
                        dv,
                        label="図面",
                    )

        # --- 計算書ドラフト ---
        with sub_t2:
            c = result.get("calc")
            if c is None:
                st.info(
                    "計算書PDFがアップロードされていないため、計算書ドラフトはありません。"
                )
            else:
                items = c.get("items", [])
                meta = c.get("_meta", {})
                st.caption(
                    f"路線: `{c.get('route', '?')}`  /  "
                    f"items 件数: {len(items)}  /  "
                    f"モデル: `{meta.get('model', '?')}`  /  "
                    f"所要: {meta.get('elapsed_s', '?')}s"
                )
                if items:
                    st.dataframe(_indexed_dataframe(items), use_container_width=True, height=400)
                else:
                    st.warning("items が空でした。")

                # 検出位置オーバーレイ
                if items:
                    with st.expander("📍 検出位置（PDFのどこから読んだか）", expanded=False):
                        _render_overlay_section(
                            st.session_state.get("upload_calc_bytes"),
                            items,
                            label="計算書",
                        )

        # --- 整合性 ---
        with sub_t3:
            con = result.get("consistency")
            if con is None:
                st.info("計算書PDFがアップロードされた場合のみ整合性チェックが実行されます。")
            else:
                s = con.get("summary", {})
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("F1", f"{s.get('f1', 0):.3f}")
                col2.metric("再現率", f"{s.get('recall', 0):.3f}")
                col3.metric("適合率", f"{s.get('precision', 0):.3f}")
                col4.metric(
                    "マッチ数",
                    f"{s.get('matched', 0)} / {s.get('calc_length_items', 0)}",
                )
                st.markdown("##### ✅ マッチした項目")
                if con.get("matches"):
                    rows = [
                        {
                            "計算書": f"{m['calc'].get('L4', '')} {m['calc'].get('規格', '')}",
                            "計算書数量": m["calc"].get("数量"),
                            "図面値": m["drawing"].get("value"),
                            "図面コンテキスト": m["drawing"].get("context", ""),
                        }
                        for m in con["matches"]
                    ]
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)
                else:
                    st.info("マッチなし")
                with st.expander("⚠️ 計算書側で未マッチ"):
                    st.json(con.get("unmatched_calc", []))
                with st.expander("⚠️ 図面側で未マッチ"):
                    st.json(con.get("unmatched_drawing", []))

        # --- 生JSON ---
        with sub_t4:
            st.markdown("##### 図面抽出 raw")
            st.json(result.get("drawing"))
            if result.get("calc") is not None:
                st.markdown("##### 計算書抽出 raw")
                st.json(result.get("calc"))
            if result.get("consistency") is not None:
                st.markdown("##### 整合性チェック raw")
                st.json(result.get("consistency"))

        if st.button("🗑 結果をクリア", key="upload_clear_button"):
            for k in (
                "upload_result",
                "upload_route_used",
                "upload_drawing_filename",
                "upload_calc_filename",
                "upload_drawing_bytes",
                "upload_calc_bytes",
            ):
                st.session_state.pop(k, None)
            st.rerun()

with tab_overview:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"📍 ケース: {case_id}（路線 {route}）")
        st.markdown(
            f"""
- **工事**: 那珂（那珂二丁目外）地区下水道築造工事
- **発注**: 福岡市道路下水道局 建設部 東部下水道課
- **対象工種**: 管きょ更生工（更生自立管）
- **路線**: `{route}`
"""
        )
        gt = load_json(paths.case_dir(case_id) / "ground_truth.json")
        if gt:
            st.success(f"✅ Ground Truth あり（{len(gt.get('detected_items', []))} 項目）")
        else:
            st.warning("⚠️ Ground Truth なし（case_001-003 のみ作成済み）")

    with col2:
        st.subheader("📁 入力PDF")
        show_pdf_preview("数量計算書", paths.case_calc_pdf(case_id))
        show_pdf_preview("図面", paths.case_drawing_pdf(case_id))

    # 検出位置オーバーレイ（案件PDFと抽出結果から）
    st.divider()
    st.subheader("📍 検出位置（PDFのどこから読んだか）")
    extracted_drawing = load_json(paths.case_results_dir(case_id) / "extracted_drawing.json") or {}
    extracted_calc = load_json(paths.case_results_dir(case_id) / "extracted_calc_book.json") or {}
    has_drawing = bool(extracted_drawing.get("detected_values"))
    has_calc = bool(extracted_calc.get("items"))
    if not (has_drawing or has_calc):
        st.info("まだ抽出が実行されていません。サイドバーから抽出を実行してください。")
    else:
        ov_t1, ov_t2 = st.tabs(["🖼 図面", "📄 計算書"])
        with ov_t1:
            if has_drawing:
                _render_overlay_section(
                    _read_pdf_bytes(paths.case_drawing_pdf(case_id)),
                    extracted_drawing.get("detected_values", []),
                    label="図面",
                )
            else:
                st.info("図面抽出が未実行です。サイドバーの『図面抽出（Gemini）』を押してください。")
        with ov_t2:
            if has_calc:
                _render_overlay_section(
                    _read_pdf_bytes(paths.case_calc_pdf(case_id)),
                    extracted_calc.get("items", []),
                    label="計算書",
                )
            else:
                st.info("計算書抽出が未実行です。サイドバーの『計算書抽出（Gemini）』を押してください。")


with tab_calc:
    st.subheader("📄 数量計算書ドラフト")
    pred = load_json(paths.case_results_dir(case_id) / "extracted_calc_book.json")
    if pred is None:
        st.info("まだ計算書抽出が実行されていません。サイドバーの『計算書抽出（Gemini）』を押してください。")
    else:
        items = pred.get("items", [])
        if items:
            df = _indexed_dataframe(items)
            st.dataframe(df, use_container_width=True, height=400)
            st.caption(f"路線: `{pred.get('route')}` / モデル: `{pred.get('_meta', {}).get('model', '?')}` / 所要: {pred.get('_meta', {}).get('elapsed_s', '?')}s")
            st.caption("`#` 列は『概要』タブの 📍 検出位置 オーバーレイ番号と一致します")
        else:
            st.warning("items が空です")
        with st.expander("生JSON表示"):
            st.json(pred)


with tab_soukatu:
    st.subheader("📊 数量総括表（L2-L3-L4 集計）")
    csv_path = paths.RESULTS_DIR / "_summary" / "soukatu_aggregated.csv"
    if not csv_path.exists():
        st.info("まだ集計が実行されていません。サイドバーから『一括実行』するか、CLI で `aggregate` を実行してください。")
    else:
        df = pd.read_csv(csv_path)
        L2_filter = st.multiselect("L2フィルタ", df["L2"].dropna().unique().tolist(), default=[])
        view = df.copy()
        if L2_filter:
            view = view[view["L2"].isin(L2_filter)]
        st.dataframe(view, use_container_width=True, height=500)
        st.caption(f"全 {len(df)} 行 / 表示 {len(view)} 行")
        st.download_button(
            "💾 CSV ダウンロード",
            csv_path.read_bytes(),
            file_name="soukatu_aggregated.csv",
            mime="text/csv",
        )


with tab_check:
    st.subheader("🔍 整合性チェック（計算書 vs 図面）")
    rep = load_json(paths.case_results_dir(case_id) / "consistency_report.json")
    if rep is None:
        st.info("まだ整合性チェックが実行されていません。")
    elif rep.get("skipped"):
        st.warning(f"スキップ: {rep.get('reason')}")
    else:
        s = rep.get("summary", {})
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("F1", f"{s.get('f1', 0):.3f}")
        col2.metric("再現率", f"{s.get('recall', 0):.3f}")
        col3.metric("適合率", f"{s.get('precision', 0):.3f}")
        col4.metric(
            "マッチ数",
            f"{s.get('matched', 0)} / {s.get('calc_length_items', 0)}",
        )

        st.markdown("### ✅ マッチした項目")
        if rep.get("matches"):
            rows = []
            for m in rep["matches"]:
                rows.append({
                    "計算書": f"{m['calc'].get('L4', '')} {m['calc'].get('規格', '')}",
                    "計算書数量": m['calc'].get("数量"),
                    "図面値": m['drawing'].get('value'),
                    "図面コンテキスト": m['drawing'].get('context', ''),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("マッチなし")

        with st.expander("⚠️ 計算書側で未マッチの項目"):
            st.json(rep.get("unmatched_calc", []))
        with st.expander("⚠️ 図面側で未マッチの項目"):
            st.json(rep.get("unmatched_drawing", []))


with tab_eval:
    st.subheader("📊 精度メトリクス（GT 突合）")
    overall = load_json(paths.RESULTS_DIR / "_summary" / "eval_overall.json")
    case_eval = load_json(paths.case_results_dir(case_id) / "eval_report.json")

    if overall and overall.get("overall"):
        st.markdown("### 全体（マクロ平均）")
        o = overall["overall"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Macro F1", f"{o.get('macro_f1', 0):.3f}")
        col2.metric("Macro 再現率", f"{o.get('macro_recall', 0):.3f}")
        col3.metric("Macro 適合率", f"{o.get('macro_precision', 0):.3f}")
        col4.metric("評価ケース数", o.get("n_cases", 0))

        # Go/No-Go 帯
        macro_f1 = o.get("macro_f1", 0)
        if macro_f1 >= 0.65:
            st.success("✅ **Go閾値達成**（F1 ≥ 0.65）→ Phase 1 即着手の判定材料")
        elif macro_f1 >= 0.50:
            st.warning("⚠️ **Conditional Go**（F1 0.50-0.64）→ 領域別再投資検討")
        else:
            st.error("❌ **No-Go閾値**（F1 < 0.50）→ 原因切り分け or パートナー連携検討")

        st.markdown("### ケース別")
        if overall.get("cases"):
            rows = []
            for c in overall["cases"]:
                rows.append({
                    "case": c.get("case_id"),
                    "F1": c.get("f1"),
                    "P": c.get("precision"),
                    "R": c.get("recall"),
                    "TP": c.get("tp"),
                    "GT": c.get("n_gt"),
                    "Pred": c.get("n_pred"),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

    if case_eval:
        st.markdown(f"### このケース（{case_id}）の詳細")
        col1, col2, col3 = st.columns(3)
        col1.metric("F1", f"{case_eval.get('f1', 0):.3f}")
        col2.metric("再現率", f"{case_eval.get('recall', 0):.3f}")
        col3.metric("適合率", f"{case_eval.get('precision', 0):.3f}")
        with st.expander("FN（GTにあるが検出されなかった）"):
            st.json(case_eval.get("false_negatives", []))
        with st.expander("FP（検出されたがGTにない）"):
            st.json(case_eval.get("false_positives", []))

    if not overall and not case_eval:
        st.info("まだ評価が実行されていません。サイドバーから『一括実行』するか『GT 評価』を押してください。")


# ---------- フッター ----------
st.divider()
st.caption(
    f"📂 PoC ROOT: `{POC_ROOT.relative_to(POC_ROOT.parents[3])}`  •  "
    f"GEMINI_MODEL_PRIMARY=`{os.environ.get('GEMINI_MODEL_PRIMARY', '(default)')}`  •  "
    f"API_KEY設定={'✅' if os.environ.get('GEMINI_API_KEY') else '❌（.envを設定）'}"
)
