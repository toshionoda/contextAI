"""課題抽出ログの中核。

計画書（/Users/nodatoshio/.claude/plans/cuddly-roaming-pie.md）の「課題抽出の仕組み」
に沿って、1件1ファイルの frontmatter 付き Markdown を `issues/open/` に書き出す。
Track A（Rust）からは CLI 経由 or 直接ファイル書き出しで同じ形式を使う。
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ed_agent.config import ISSUES_OPEN_DIR


JST = timezone(timedelta(hours=9))

ALLOWED_CATEGORIES = {
    # Track A
    "format-spec-gap",
    "version-specific-quirk",
    "entity-unsupported",
    "roundtrip-mismatch",
    "encoding-issue",
    "perf-bottleneck",
    # Track B
    "knowledge-gap",
    "llm-hallucination",
    "dtd-mismatch",
    "encoding",
    "spec-ambiguity",
    "tool-limit",
}

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_FIELD_RE = re.compile(r"^([a-zA-Z_]+):\s*(.*)$")


def _next_id(now: datetime) -> str:
    date_part = now.strftime("%Y%m%d")
    existing = list(ISSUES_OPEN_DIR.glob(f"ISS-{date_part}-*.md"))
    seq = len(existing) + 1
    return f"ISS-{date_part}-{seq:03d}"


def create_issue(
    *,
    track: str,
    severity: str,
    category: str,
    source: str,
    project: str = "",
    file: str = "",
    phenomenon: str,
    decision: str,
    reason_for_human: str,
    hypothesis: str,
) -> Path:
    if category not in ALLOWED_CATEGORIES:
        # 未知カテゴリも受け入れるが警告（将来カテゴリ拡張に備える）
        print(f"warning: unknown category '{category}'. adding anyway.")

    ISSUES_OPEN_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=JST)
    issue_id = _next_id(now)
    path = ISSUES_OPEN_DIR / f"{issue_id}.md"

    body = f"""---
id: {issue_id}
track: {track}
severity: {severity}
category: {category}
source: {source}
project: {project}
file: {file}
created: {now.isoformat(timespec='seconds')}
---

## 現象
{phenomenon}

## Agentの判断
{decision}

## 人間の判断が必要な理由
{reason_for_human}

## 改善仮説
{hypothesis}
"""
    path.write_text(body, encoding="utf-8")
    return path


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        fm = _FIELD_RE.match(line)
        if fm:
            fields[fm.group(1)] = fm.group(2).strip()
    return fields


def summarize_open() -> str:
    if not ISSUES_OPEN_DIR.exists():
        return "no issues directory yet.\n"

    files = sorted(ISSUES_OPEN_DIR.glob("ISS-*.md"))
    if not files:
        return "no open issues.\n"

    by_track: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_source: Counter[str] = Counter()

    for f in files:
        meta = _parse_frontmatter(f.read_text(encoding="utf-8"))
        by_track[meta.get("track", "?")] += 1
        by_severity[meta.get("severity", "?")] += 1
        by_category[meta.get("category", "?")] += 1
        by_source[meta.get("source", "?")] += 1

    lines = [f"# Open issues: {len(files)}", ""]
    for label, counter in [
        ("by track", by_track),
        ("by severity", by_severity),
        ("by category", by_category),
        ("by source", by_source),
    ]:
        lines.append(f"## {label}")
        for k, v in counter.most_common():
            lines.append(f"- {k}: {v}")
        lines.append("")
    return "\n".join(lines)
