"""Provider-neutral domain model.

All datetimes are timezone-aware UTC. A score keeps regulation time (90 minutes
plus stoppage time), extra time and a penalty shoot-out apart, so no statistic
mixes them silently. Provider adapters translate their payloads into these
types; nothing outside an adapter depends on a provider's field names or IDs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

CompetitionKind = Literal["league", "domestic_cup", "continental"]
MatchStatus = Literal["scheduled", "finished", "postponed", "cancelled"]
Side = Literal["home", "away"]
VenueType = Literal["home", "away", "neutral"]


@dataclass(frozen=True)
class Competition:
    id: str
    name: str
    kind: CompetitionKind
    country: str | None = None


@dataclass(frozen=True)
class Team:
    id: str
    name: str
    short_name: str
    country: str


@dataclass(frozen=True)
class Score:
    """Goals by side.

    ``*_90`` is the result after regulation time. ``*_aet`` is the cumulative
    result after extra time and is ``None`` when extra time was not played.
    ``*_pens`` holds shoot-out goals and is ``None`` without a shoot-out.
    """

    home_90: int
    away_90: int
    home_aet: int | None = None
    away_aet: int | None = None
    home_pens: int | None = None
    away_pens: int | None = None

    @property
    def extra_time(self) -> bool:
        return self.home_aet is not None and self.away_aet is not None

    @property
    def shootout(self) -> bool:
        return self.home_pens is not None and self.away_pens is not None

    def goals(self, side: Side, include_extra_time: bool) -> tuple[int, int]:
        """Return (goals for, goals against) for ``side``; never counts penalties."""
        if include_extra_time and self.extra_time:
            home, away = self.home_aet, self.away_aet
        else:
            home, away = self.home_90, self.away_90
        assert home is not None and away is not None
        return (home, away) if side == "home" else (away, home)

    def winner_of_tie(self) -> Side | None:
        """Side that won after extra time or penalties; ``None`` for a draw."""
        home, away = self.goals("home", include_extra_time=True)
        if home == away and self.shootout:
            assert self.home_pens is not None and self.away_pens is not None
            home, away = self.home_pens, self.away_pens
        if home == away:
            return None
        return "home" if home > away else "away"


@dataclass(frozen=True)
class TeamMatchStats:
    """One team's match statistics. ``None`` means the provider did not supply it.

    ``includes_extra_time`` is true when the provider's totals cover extra-time
    minutes; such rows are excluded from regulation-time averages.
    """

    corners: int | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None
    shots: int | None = None
    shots_on_target: int | None = None
    includes_extra_time: bool = False


@dataclass(frozen=True)
class Match:
    id: str
    competition_id: str
    season: str
    round: str | None
    kickoff: datetime
    home_id: str
    away_id: str
    venue: str
    neutral_venue: bool
    status: MatchStatus
    score: Score | None = None
    home_stats: TeamMatchStats | None = None
    away_stats: TeamMatchStats | None = None

    def involves(self, team_id: str) -> bool:
        return team_id in (self.home_id, self.away_id)

    def side(self, team_id: str) -> Side:
        if team_id == self.home_id:
            return "home"
        if team_id == self.away_id:
            return "away"
        raise ValueError(f"team {team_id} did not play match {self.id}")

    def venue_type(self, team_id: str) -> VenueType:
        if self.neutral_venue:
            return "neutral"
        return self.side(team_id)

    def opponent(self, team_id: str) -> str:
        return self.away_id if self.side(team_id) == "home" else self.home_id

    def stats_for(self, team_id: str) -> tuple[TeamMatchStats | None, TeamMatchStats | None]:
        """Return (own stats, opponent stats) from ``team_id``'s perspective."""
        if self.side(team_id) == "home":
            return self.home_stats, self.away_stats
        return self.away_stats, self.home_stats


@dataclass(frozen=True)
class CoachSpell:
    team_id: str
    coach: str
    start: date
    end: date | None = None


@dataclass(frozen=True)
class Absence:
    """A reported absence. ``status`` expresses confidence, not severity."""

    team_id: str
    player: str
    reason: Literal["injury", "suspension", "other"]
    status: Literal["confirmed", "doubtful"]
    importance: Literal["key", "regular", "unknown"]
    source: str
    updated_at: datetime


@dataclass(frozen=True)
class LineupInfo:
    match_id: str
    team_id: str
    status: Literal["not_available", "predicted", "confirmed"]
    updated_at: datetime | None = None
