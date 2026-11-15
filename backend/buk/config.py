"""Runtime settings from environment variables (names only; no secret values).

BUK_DATA_SOURCE  data provider; only "demo" exists in the foundation.
BUK_WEB_DIST     optional path to the built web app (web/dist) to serve.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_source: str = "demo"
    web_dist: Path | None = None


def load_settings() -> Settings:
    web_dist = os.environ.get("BUK_WEB_DIST")
    return Settings(
        data_source=os.environ.get("BUK_DATA_SOURCE", "demo"),
        web_dist=Path(web_dist).resolve() if web_dist else None,
    )
