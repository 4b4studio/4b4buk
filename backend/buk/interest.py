"""Transparent, rule-based ranking of matches into separate lists.

The watch list and the analysis list are scored independently, and every point
comes from a named reason with parameters. The UI renders reasons from these
codes; the assistant quotes the same codes. There is no odds list until a
licensed odds source and a validated probability model exist: the foundation
returns an explicit NO_ODDS_SOURCE status instead of guessing.

Personalisation boundary: followed teams and competitions raise the watch
score only. Nothing here learns from betting behaviour or rewards higher odds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Mapping, Sequence

from .domain import Match
from .providers.base import Dataset
from .stats import (
    LOCAL_TZ,
    SampleFilter,
    StandingRow,
    average,
    coach_on,
    h2h,
    schedule_context,
    standings,
)

WEIGHTS: dict[str, float] = {
    # watch list
    "FOLLOWED_TEAM": 3.0,
    "FOLLOWED_COMPETITION": 1.0,
    "TOP_CLASH": 2.0,
    "RELEGATION_BATTLE": 1.0,
    "CLOSE_IN_TABLE": 1.0,
    "HIGH_SCORING": 1.0,
    "KNOCKOUT": 2.0,
    "DISCOVERY": 0.5,
    # analysis list
    "SHORT_REST": 1.5,
    "REST_GAP": 1.0,
    "CONTINENTAL_BEFORE": 1.0,
    "CONTINENTAL_AFTER": 1.0,
    "CUP_BEFORE": 0.5,
    "CUP_AFTER": 0.5,
    "PREV_EXTRA_TIME": 1.0,
    "PREV_SHOOTOUT": 1.0,
    "NEW_COACH": 1.0,
    "KEY_ABSENCES": 1.0,
    "HIGH_CORNERS": 1.0,
    "LOW_CORNERS": 0.5,
    "HIGH_CARDS": 1.0,
}
SCHEDULE_REASONS = ("SHORT_REST", "CONTINENTAL_BEFORE", "CONTINENTAL_AFTER", "CUP_BEFORE", "CUP_AFTER", "PREV_EXTRA_TIME", "PREV_SHOOTOUT")
TOP_POSITIONS = 4
BOTTOM_POSITIONS = 3
HIGH_SCORING_GOALS = 3.0
HIGH_CORNERS_TOTAL = 11.5
LOW_CORNERS_TOTAL = 7.5
HIGH_CARDS_TOTAL = 5.5
NEW_COACH_DAYS = 60
REST_GAP_DAYS = 3


@dataclass(frozen=True)
class Profile:
    followed_teams: frozenset[str] = frozenset()
    followed_competitions: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Reason:
    code: str
    weight: float
    params: dict[str, str | int | float] = field(default_factory=dict)


@dataclass(frozen=True)
class ListScore:
    score: float
    reasons: tuple[Reason, ...]


@dataclass(frozen=True)
class Interest:
    match_id: str
    watch: ListScore
    analysis: ListScore
    warnings: tuple[Reason, ...]
    followed: bool
    discovery: bool


def _reason(code: str, **params: str | int | float) -> Reason:
    return Reason(code=code, weight=WEIGHTS.get(code, 0.0), params=params)


def _table_index(rows: Sequence[StandingRow]) -> dict[str, StandingRow]:
    return {row.team_id: row for row in rows}


def league_tables(dataset: Dataset, matches: Sequence[Match], before: datetime) -> dict[tuple[str, str], list[StandingRow]]:
    names = {team_id: team.name for team_id, team in dataset.teams.items()}
    tables: dict[tuple[str, str], list[StandingRow]] = {}
    for match in matches:
        competition = dataset.competitions.get(match.competition_id)
        key = (match.competition_id, match.season)
        if competition and competition.kind == "league" and key not in tables:
            tables[key] = standings(dataset.matches, match.competition_id, match.season, before, names)
    return tables


def score_match(
    dataset: Dataset,
    match: Match,
    profile: Profile,
    tables: Mapping[tuple[str, str], list[StandingRow]],
) -> Interest:
    competitions = dataset.competitions
    competition = competitions.get(match.competition_id)
    before = match.kickoff
    watch: list[Reason] = []
    analysis: list[Reason] = []
    warnings: list[Reason] = []
    teams = (match.home_id, match.away_id)

    followed_teams = [t for t in teams if t in profile.followed_teams]
    for team_id in followed_teams:
        watch.append(_reason("FOLLOWED_TEAM", team=team_id))
    if match.competition_id in profile.followed_competitions:
        watch.append(_reason("FOLLOWED_COMPETITION", competition=match.competition_id))

    if competition and competition.kind == "league":
        table = _table_index(tables.get((match.competition_id, match.season), []))
        home, away = table.get(match.home_id), table.get(match.away_id)
        size = len(table)
        if home and away and home.played and away.played:
            if home.position <= TOP_POSITIONS and away.position <= TOP_POSITIONS:
                watch.append(_reason("TOP_CLASH", pos_home=home.position, pos_away=away.position))
            elif home.position > size - BOTTOM_POSITIONS and away.position > size - BOTTOM_POSITIONS:
                watch.append(_reason("RELEGATION_BATTLE", pos_home=home.position, pos_away=away.position))
            elif abs(home.points - away.points) <= 2:
                watch.append(_reason("CLOSE_IN_TABLE", gap=abs(home.points - away.points)))
    elif competition is not None:
        watch.append(_reason("KNOCKOUT", competition=competition.id))

    goal_filter = SampleFilter(window=10)
    totals = [
        average(dataset.matches, t, "goals", "total", before, competitions, goal_filter) for t in teams
    ]
    if all(a.value is not None for a in totals):
        combined = round((totals[0].value + totals[1].value) / 2, 2)  # type: ignore[operator]
        if combined >= HIGH_SCORING_GOALS:
            watch.append(_reason("HIGH_SCORING", avg=combined))
    if any("SMALL_SAMPLE" in a.warnings for a in totals):
        warnings.append(_reason("SMALL_SAMPLE"))

    contexts = {t: schedule_context(dataset.matches, t, match, competitions) for t in teams}
    for team_id, context in contexts.items():
        for flag in context.flags:
            if flag in SCHEDULE_REASONS:
                days = context.days_since_previous if flag.endswith("BEFORE") or flag.startswith(("PREV", "SHORT")) else context.days_to_next
                analysis.append(_reason(flag, team=team_id, days=days if days is not None else -1))
    rest = {t: c.days_since_previous for t, c in contexts.items()}
    if all(value is not None for value in rest.values()):
        home_rest, away_rest = rest[match.home_id], rest[match.away_id]
        assert home_rest is not None and away_rest is not None
        if abs(home_rest - away_rest) >= REST_GAP_DAYS:
            fresher = match.home_id if home_rest > away_rest else match.away_id
            analysis.append(_reason("REST_GAP", team=fresher, diff=abs(home_rest - away_rest)))

    match_day: date = match.kickoff.astimezone(LOCAL_TZ).date()
    for team_id in teams:
        spell = coach_on(dataset.coaches, team_id, match_day)
        if spell is not None and (match_day - spell.start).days <= NEW_COACH_DAYS:
            analysis.append(_reason("NEW_COACH", team=team_id, days=(match_day - spell.start).days))
        key_out = [
            a for a in dataset.absences if a.team_id == team_id and a.status == "confirmed" and a.importance == "key"
        ]
        if key_out:
            analysis.append(_reason("KEY_ABSENCES", team=team_id, count=len(key_out)))

    corner_parts = [
        average(dataset.matches, match.home_id, "corners", "for", before, competitions, SampleFilter(venue="home")),
        average(dataset.matches, match.away_id, "corners", "against", before, competitions, SampleFilter(venue="away")),
        average(dataset.matches, match.away_id, "corners", "for", before, competitions, SampleFilter(venue="away")),
        average(dataset.matches, match.home_id, "corners", "against", before, competitions, SampleFilter(venue="home")),
    ]
    if all(part.value is not None and part.n_used >= 3 for part in corner_parts):
        home_side = (corner_parts[0].value + corner_parts[1].value) / 2  # type: ignore[operator]
        away_side = (corner_parts[2].value + corner_parts[3].value) / 2  # type: ignore[operator]
        corner_total = round(home_side + away_side, 1)
        if corner_total >= HIGH_CORNERS_TOTAL:
            analysis.append(_reason("HIGH_CORNERS", total=corner_total))
        elif corner_total <= LOW_CORNERS_TOTAL:
            analysis.append(_reason("LOW_CORNERS", total=corner_total))

    cards = [average(dataset.matches, t, "cards", "for", before, competitions, SampleFilter()) for t in teams]
    if all(c.value is not None and c.n_used >= 3 for c in cards):
        card_total = round(cards[0].value + cards[1].value, 1)  # type: ignore[operator]
        if card_total >= HIGH_CARDS_TOTAL:
            analysis.append(_reason("HIGH_CARDS", total=card_total))

    history = h2h(dataset.matches, match.home_id, match.away_id, before, dataset.coaches)
    for code in history.warnings:
        if code in ("H2H_STALE", "H2H_NONE", "COACH_CHANGED_SINCE_LAST"):
            params: dict[str, str | int | float] = {}
            if history.days_since_last is not None:
                params["days"] = history.days_since_last
            warnings.append(Reason(code=code, weight=0.0, params=params))

    return Interest(
        match_id=match.id,
        watch=ListScore(score=round(sum(r.weight for r in watch), 2), reasons=_ordered(watch)),
        analysis=ListScore(score=round(sum(r.weight for r in analysis), 2), reasons=_ordered(analysis)),
        warnings=tuple(warnings),
        followed=bool(followed_teams) or match.competition_id in profile.followed_competitions,
        discovery=False,
    )


def _ordered(reasons: list[Reason]) -> tuple[Reason, ...]:
    return tuple(sorted(reasons, key=lambda r: -r.weight))


def matches_on(dataset: Dataset, day: date) -> list[Match]:
    """Matches whose Europe/Warsaw calendar date is ``day``."""
    return sorted(
        (m for m in dataset.matches if m.kickoff.astimezone(LOCAL_TZ).date() == day),
        key=lambda m: (m.kickoff, m.id),
    )


def rank_day(dataset: Dataset, day: date, profile: Profile) -> tuple[list[Match], dict[str, Interest]]:
    """Score every match of the day and mark one discovery outside the user's interests."""
    day_matches = matches_on(dataset, day)
    if not day_matches:
        return [], {}
    reference = min(m.kickoff for m in day_matches)
    tables = league_tables(dataset, day_matches, reference)
    scores = {m.id: score_match(dataset, m, profile, tables) for m in day_matches}
    outside = [m for m in day_matches if not scores[m.id].followed]
    if outside and (profile.followed_teams or profile.followed_competitions):
        best = max(outside, key=lambda m: (scores[m.id].watch.score + scores[m.id].analysis.score, -m.kickoff.timestamp()))
        current = scores[best.id]
        if current.watch.score + current.analysis.score > 0:
            discovery_reason = _reason("DISCOVERY", competition=best.competition_id)
            scores[best.id] = Interest(
                match_id=current.match_id,
                watch=ListScore(
                    score=round(current.watch.score + discovery_reason.weight, 2),
                    reasons=_ordered([*current.watch.reasons, discovery_reason]),
                ),
                analysis=current.analysis,
                warnings=current.warnings,
                followed=current.followed,
                discovery=True,
            )
    return day_matches, scores


def ordered_ids(matches: Sequence[Match], scores: Mapping[str, Interest], list_name: str) -> list[str]:
    def key(match: Match) -> tuple[float, float]:
        score = getattr(scores[match.id], list_name).score
        return (-score, match.kickoff.timestamp())

    return [m.id for m in sorted(matches, key=key)]
