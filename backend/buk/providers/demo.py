"""Demonstration provider backed by a generated JSON file.

All teams, players, coaches and results in the demo file are fictional. The
file is produced deterministically by ``scripts/make_demo_data.py``.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from ..domain import Absence, CoachSpell, Competition, LineupInfo, Match, Score, Team, TeamMatchStats
from .base import Dataset

DEMO_FILE = Path(__file__).resolve().parent.parent / "demo" / "demo_data.json"


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"datetime without timezone: {value}")
    return parsed


def _stats(raw: dict[str, Any] | None) -> TeamMatchStats | None:
    return TeamMatchStats(**raw) if raw is not None else None


def _match(raw: dict[str, Any]) -> Match:
    score = raw.get("score")
    return Match(
        id=raw["id"],
        competition_id=raw["competition_id"],
        season=raw["season"],
        round=raw.get("round"),
        kickoff=_dt(raw["kickoff"]),
        home_id=raw["home_id"],
        away_id=raw["away_id"],
        venue=raw["venue"],
        neutral_venue=bool(raw.get("neutral_venue", False)),
        status=raw["status"],
        score=Score(**score) if score is not None else None,
        home_stats=_stats(raw.get("home_stats")),
        away_stats=_stats(raw.get("away_stats")),
    )


def parse_dataset(payload: dict[str, Any], source: str = "demo") -> Dataset:
    meta = payload["meta"]
    return Dataset(
        source=source,
        label=meta["label"],
        as_of=_dt(meta["as_of"]),
        competitions={c["id"]: Competition(**c) for c in payload["competitions"]},
        teams={t["id"]: Team(**t) for t in payload["teams"]},
        matches=tuple(_match(m) for m in payload["matches"]),
        coaches=tuple(
            CoachSpell(
                team_id=c["team_id"],
                coach=c["coach"],
                start=date.fromisoformat(c["start"]),
                end=date.fromisoformat(c["end"]) if c.get("end") else None,
            )
            for c in payload.get("coaches", [])
        ),
        absences=tuple(
            Absence(**{**a, "updated_at": _dt(a["updated_at"])}) for a in payload.get("absences", [])
        ),
        lineups=tuple(
            LineupInfo(
                match_id=l["match_id"],
                team_id=l["team_id"],
                status=l["status"],
                updated_at=_dt(l["updated_at"]) if l.get("updated_at") else None,
            )
            for l in payload.get("lineups", [])
        ),
        is_demo=bool(meta.get("demo", False)),
        default_profile=meta.get("default_profile", {}),
        absence_coverage=frozenset(meta.get("absence_coverage", [])),
    )


class DemoProvider:
    name = "demo"

    def __init__(self, path: Path = DEMO_FILE) -> None:
        self.path = path

    def load(self) -> Dataset:
        with self.path.open(encoding="utf-8") as handle:
            return parse_dataset(json.load(handle), source=self.name)
