"""Data-provider boundary.

A provider adapter turns one external source into the provider-neutral domain
model. In the foundation the whole dataset is held in memory; the planned
storage package replaces this with PostgreSQL tables filled by scheduled
ingestion jobs, while the statistics engine keeps the same inputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from ..domain import Absence, CoachSpell, Competition, LineupInfo, Match, Team


@dataclass(frozen=True)
class Dataset:
    source: str
    label: str
    as_of: datetime
    competitions: dict[str, Competition]
    teams: dict[str, Team]
    matches: tuple[Match, ...]
    coaches: tuple[CoachSpell, ...] = ()
    absences: tuple[Absence, ...] = ()
    lineups: tuple[LineupInfo, ...] = ()
    is_demo: bool = False
    default_profile: dict[str, list[str]] = field(default_factory=dict)
    # Teams whose absences the source reports; others are "no data", not "none".
    absence_coverage: frozenset[str] = frozenset()

    def match(self, match_id: str) -> Match | None:
        return next((m for m in self.matches if m.id == match_id), None)


class DataProvider(Protocol):
    """Implemented by each source adapter (demo, and later licensed APIs)."""

    name: str

    def load(self) -> Dataset:
        """Return a consistent snapshot of the provider's data."""
        ...
