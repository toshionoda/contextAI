"""パス・モデル設定。環境変数は `.env` から。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_DIR = PROJECT_ROOT / "references"
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
SAMPLES_DIR = PROJECT_ROOT / "samples"
OUTPUT_DIR = PROJECT_ROOT / "output"
ISSUES_DIR = PROJECT_ROOT / "issues"
ISSUES_OPEN_DIR = ISSUES_DIR / "open"
ISSUES_RESOLVED_DIR = ISSUES_DIR / "resolved"


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    model: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
            model=os.environ.get("ED_AGENT_MODEL", "claude-opus-4-7"),
        )
