"""Gemini Vision のシンプルなラッパー。

- PDF をそのまま `inline_data` で投入する
- response_mime_type=application/json でJSON出力を強制
- プライマリモデルが失敗したらフォールバックに切替
- 簡易リトライとログ
- Self-Consistency (k回サンプリング → 多数決) も提供
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class GeminiCallResult:
    text: str
    model: str
    raw: Any
    elapsed_s: float

    def parse_json(self) -> Any:
        # gemini が text に JSON を返す前提
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as e:
            # コードフェンスを含む場合の救済
            stripped = self.text.strip()
            for fence in ("```json", "```"):
                if stripped.startswith(fence):
                    stripped = stripped[len(fence):]
                if stripped.endswith("```"):
                    stripped = stripped[: -len("```")]
            stripped = stripped.strip()
            return json.loads(stripped)


class GeminiClient:
    """軽量ラッパー。google-genai SDK が利用可能なら使う。"""

    def __init__(self, api_key: str | None = None, primary: str | None = None, fallback: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY が設定されていません。.env または環境変数で設定してください。"
            )
        self.primary = primary or os.environ.get("GEMINI_MODEL_PRIMARY", "gemini-3-flash-preview")
        self.fallback = fallback or os.environ.get("GEMINI_MODEL_FALLBACK", "gemini-2.5-flash")

        try:
            from google import genai  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("google-genai がインストールされていません: pip install google-genai") from e
        self._genai = genai
        self._client = genai.Client(api_key=self.api_key)

    def generate_json(
        self,
        prompt: str,
        pdf_path: Path | None = None,
        response_schema: dict | None = None,
        temperature: float = 0.0,
        max_retries: int = 2,
    ) -> GeminiCallResult:
        """PDFを添えてJSON生成。pdf_pathがNoneならテキスト生成のみ。"""
        last_err: Exception | None = None
        for model in (self.primary, self.fallback):
            for attempt in range(max_retries):
                try:
                    return self._generate_once(model, prompt, pdf_path, response_schema, temperature)
                except Exception as e:
                    last_err = e
                    logger.warning("Gemini error (model=%s, attempt=%d): %s", model, attempt + 1, e)
                    time.sleep(1.0 + attempt)
        raise RuntimeError(f"Gemini call failed after retries: {last_err}")

    def _generate_once(
        self,
        model: str,
        prompt: str,
        pdf_path: Path | None,
        response_schema: dict | None,
        temperature: float,
    ) -> GeminiCallResult:
        from google.genai import types  # type: ignore

        parts: list[Any] = []
        if pdf_path is not None:
            data = pdf_path.read_bytes()
            parts.append(types.Part.from_bytes(data=data, mime_type="application/pdf"))
        parts.append(prompt)

        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "response_mime_type": "application/json",
        }
        if response_schema is not None:
            config_kwargs["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_kwargs)

        t0 = time.time()
        resp = self._client.models.generate_content(
            model=model, contents=parts, config=config,
        )
        elapsed = time.time() - t0

        text = ""
        try:
            text = resp.text or ""
        except Exception:
            # SDK のバージョンによっては candidates から拾う
            for cand in getattr(resp, "candidates", []) or []:
                content = getattr(cand, "content", None)
                if content and getattr(content, "parts", None):
                    for p in content.parts:
                        if getattr(p, "text", None):
                            text += p.text

        if not text:
            raise RuntimeError(f"Gemini returned empty response (model={model})")

        return GeminiCallResult(text=text, model=model, raw=resp, elapsed_s=elapsed)


def setup_logging(level: str | None = None) -> None:
    lvl = (level or os.environ.get("POC_LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


# ============================================================================
# Self-Consistency (Tier A: A4)
# ============================================================================

def _canonicalize_item(item: dict, item_keys: tuple[str, ...]) -> str:
    """1項目を多数決のためのキーに正規化する。

    数量は小数点2桁、単位は記載通り、文字列はstrip。
    """
    parts: list[str] = []
    for k in item_keys:
        v = item.get(k)
        if isinstance(v, float):
            parts.append(f"{k}={v:.2f}")
        elif v is None:
            parts.append(f"{k}=")
        else:
            parts.append(f"{k}={str(v).strip()}")
    return "|".join(parts)


def majority_vote_items(
    payloads: list[dict],
    list_key: str,
    item_keys: tuple[str, ...],
    min_votes: int = 2,
) -> tuple[list[dict], dict]:
    """k 個の payload を集約し、`list_key` 配下のアイテムを多数決で残す。

    `min_votes` 未満の票しかないアイテムは捨てる（FP削減）。

    Returns:
        (merged_items, vote_summary)
    """
    bucket: dict[str, list[dict]] = {}
    for p in payloads:
        for item in p.get(list_key, []) or []:
            key = _canonicalize_item(item, item_keys)
            bucket.setdefault(key, []).append(item)

    merged: list[dict] = []
    vote_detail: list[dict] = []
    for key, group in bucket.items():
        votes = len(group)
        kept = votes >= min_votes
        if kept:
            # 最初の出現を代表として採用（source等の付帯情報を保持）
            merged.append(group[0])
        vote_detail.append({"key": key, "votes": votes, "kept": kept})

    summary = {
        "k": len(payloads),
        "min_votes": min_votes,
        "n_unique_items": len(bucket),
        "n_kept": len(merged),
        "votes": vote_detail,
    }
    return merged, summary


def self_consistency_generate(
    client: "GeminiClient",
    prompt: str,
    pdf_path: Path | None,
    response_schema: dict | None,
    list_key: str,
    item_keys: tuple[str, ...],
    k: int = 3,
    min_votes: int = 2,
    base_temperature: float = 0.2,
) -> tuple[dict, dict]:
    """同一プロンプトを k 回呼び出し、`list_key` のアイテムを多数決でフィルタする。

    1回目は temperature=base_temperature、2回目以降は微増させてサンプル多様性を確保する。
    エラーが出た回はスキップ（k 回より少ない有効サンプルでも続行）。
    """
    payloads: list[dict] = []
    elapsed_s = 0.0
    models_used: list[str] = []

    for i in range(k):
        temp = base_temperature + 0.1 * i  # 0.2 / 0.3 / 0.4 ...
        try:
            res = client.generate_json(
                prompt=prompt,
                pdf_path=pdf_path,
                response_schema=response_schema,
                temperature=temp,
            )
            payloads.append(res.parse_json())
            elapsed_s += res.elapsed_s
            models_used.append(res.model)
        except Exception as e:
            logger.warning("self-consistency sample %d failed: %s", i + 1, e)

    if not payloads:
        raise RuntimeError("self-consistency: all k samples failed")

    merged_items, vote_summary = majority_vote_items(
        payloads, list_key=list_key, item_keys=item_keys, min_votes=min_votes
    )

    # ベース payload に多数決後のアイテムを差し込む（最初の有効サンプルがテンプレート）
    base = dict(payloads[0])
    base[list_key] = merged_items
    base["_self_consistency"] = {
        "k_requested": k,
        "k_actual": len(payloads),
        "min_votes": min_votes,
        "models": models_used,
        "elapsed_s_total": round(elapsed_s, 2),
        "vote_summary": vote_summary,
    }
    return base, vote_summary
