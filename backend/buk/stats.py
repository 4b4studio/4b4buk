"""Deterministic statistics engine.

Every number the UI shows or the assistant quotes comes from these functions.
Each result carries its sample (matches used and excluded, with reasons), so a
user can audit any average. Only matches that finished before the reference
time are used, which keeps analyses free of look-ahead leakage.

Definitions (shown to users in the UI):
- Window: the last N finished matches that pass the filter. Matches with
  unusable data stay in the window and are listed as excluded; the window is
  not back-filled with older matches.
- Regulation period: 90 minutes plus stoppage time. Extra-time goals are added
  only for period "full"; shoot-out goals are never counted as goals.
- Form and points per game use 90-minute results; the outcome after extra time
  or penalties is reported separately.
- Home/away splits exclude neutral-venue matches.
- Days between matches are calendar days in Europe/Warsaw.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Literal, Mapping, Sequence
from zoneinfo import ZoneInfo

from .domain import CoachSpell, Competition, Match, Score, Side, TeamMatchStats

LOCAL_TZ = ZoneInfo("Europe/Warsaw")

Metric = Literal["goals", "corners", "cards", "yellow_cards", "red_cards", "shots", "shots_on_target"]
Perspective = Literal["for", "against", "total"]
VenueFilter = Literal["all", "home", "away"]
Period = Literal["regulation", "full"]
Result = Literal["W", "D", "L"]

METRICS: tuple[str, ...] = (
    "goals",
    "corners",
    "cards",
    "yellow_cards",
    "red_cards",
    "shots",
    "shots_on_target",
)
SMALL_SAMPLE = 5
STALE_H2H_DAYS = 730
SHORT_REST_DAYS = 3
NEAR_FIXTURE_DAYS = 4

COMPETITION_GROUPS: dict[str, tuple[str, ...]] = {
    "all": (),
    "league": ("league",),
    "cups": ("domestic_cup", "continental"),
}


@dataclass(frozen=True)
class SampleFilter:
    window: int = 10
    venue: VenueFilter = "all"
    competition_kinds: tuple[str, ...] = ()
    period: Period = "regulation"


@dataclass(frozen=True)
class SampleItem:
    match_id: str
    kickoff: datetime
    competition_id: str
    opponent_id: str
    venue: Literal["home", "away", "neutral"]
    goals_for_90: int
    goals_against_90: int
    extra_time: bool
    shootout: bool
    value: float | None
    excluded: str | None = None


@dataclass(frozen=True)
class Average:
    team_id: str
    metric: str
    perspective: str
    sample_filter: SampleFilter
    value: float | None
    n_used: int
    n_considered: int
    items: tuple[SampleItem, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FormEntry:
    match_id: str
    kickoff: datetime
    competition_id: str
    opponent_id: str
    venue: Literal["home", "away", "neutral"]
    goals_for_90: int
    goals_against_90: int
    result_90: Result
    decided_by: Literal["regulation", "extra_time", "penalties"]
    final_result: Result


@dataclass(frozen=True)
class FormSummary:
    team_id: str
    sample_filter: SampleFilter
    entries: tuple[FormEntry, ...]
    wins: int
    draws: int
    losses: int
    points_per_game: float | None
    goals_for: int
    goals_against: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class H2HMeeting:
    match_id: str
    kickoff: datetime
    competition_id: str
    home_id: str
    away_id: str
    venue: str
    neutral_venue: bool
    score: Score
    days_ago: int


@dataclass(frozen=True)
class CoachChange:
    team_id: str
    coach: str
    start: date


@dataclass(frozen=True)
class H2HSummary:
    team_a: str
    team_b: str
    meetings: tuple[H2HMeeting, ...]
    total_meetings: int
    a_wins_90: int
    draws_90: int
    b_wins_90: int
    a_goals_90: int
    b_goals_90: int
    last_meeting: H2HMeeting | None
    days_since_last: int | None
    coach_changes_since_last: tuple[CoachChange, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class FixtureRef:
    match_id: str
    kickoff: datetime
    competition_id: str
    competition_kind: str
    opponent_id: str
    venue: Literal["home", "away", "neutral"]
    status: str
    score: Score | None
    extra_time: bool
    shootout: bool


@dataclass(frozen=True)
class ScheduleContext:
    team_id: str
    previous: FixtureRef | None
    next: FixtureRef | None
    days_since_previous: int | None
    days_to_next: int | None
    matches_last_14_days: int
    flags: tuple[str, ...]


@dataclass(frozen=True)
class StandingRow:
    team_id: str
    position: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    points: int


def local_days_between(earlier: datetime, later: datetime) -> int:
    """Calendar days between two kickoffs in Europe/Warsaw (Sat -> Tue is 3)."""
    return (later.astimezone(LOCAL_TZ).date() - earlier.astimezone(LOCAL_TZ).date()).days


def _kind(competitions: Mapping[str, Competition], competition_id: str) -> str:
    competition = competitions.get(competition_id)
    return competition.kind if competition else "unknown"


def team_history(
    matches: Iterable[Match],
    team_id: str,
    before: datetime,
    competitions: Mapping[str, Competition],
    *,
    venue: VenueFilter = "all",
    competition_kinds: Sequence[str] = (),
) -> list[Match]:
    """Finished matches of ``team_id`` that kicked off before ``before``, newest first."""
    kinds = set(competition_kinds)
    selected = []
    for match in matches:
        if not match.involves(team_id) or match.status != "finished" or match.score is None:
            continue
        if match.kickoff >= before:
            continue
        if venue != "all" and match.venue_type(team_id) != venue:
            continue
        if kinds and _kind(competitions, match.competition_id) not in kinds:
            continue
        selected.append(match)
    selected.sort(key=lambda m: m.kickoff, reverse=True)
    return selected


def _stat_value(stats: TeamMatchStats | None, metric: str) -> int | None:
    if stats is None:
        return None
    if metric == "cards":
        if stats.yellow_cards is None or stats.red_cards is None:
            return None
        return stats.yellow_cards + stats.red_cards
    return getattr(stats, metric)


def _result(goals_for: int, goals_against: int) -> Result:
    if goals_for > goals_against:
        return "W"
    return "D" if goals_for == goals_against else "L"


def _sample_item(match: Match, team_id: str, value: float | None, excluded: str | None) -> SampleItem:
    assert match.score is not None
    goals_for, goals_against = match.score.goals(match.side(team_id), include_extra_time=False)
    return SampleItem(
        match_id=match.id,
        kickoff=match.kickoff,
        competition_id=match.competition_id,
        opponent_id=match.opponent(team_id),
        venue=match.venue_type(team_id),
        goals_for_90=goals_for,
        goals_against_90=goals_against,
        extra_time=match.score.extra_time,
        shootout=match.score.shootout,
        value=value,
        excluded=excluded,
    )


def average(
    matches: Iterable[Match],
    team_id: str,
    metric: str,
    perspective: Perspective,
    before: datetime,
    competitions: Mapping[str, Competition],
    sample_filter: SampleFilter = SampleFilter(),
) -> Average:
    """Average of ``metric`` per match, with the full list of matches behind it."""
    if metric not in METRICS:
        raise ValueError(f"unknown metric: {metric}")
    if perspective not in ("for", "against", "total"):
        raise ValueError(f"unknown perspective: {perspective}")
    history = team_history(
        matches,
        team_id,
        before,
        competitions,
        venue=sample_filter.venue,
        competition_kinds=sample_filter.competition_kinds,
    )[: sample_filter.window]

    items: list[SampleItem] = []
    used: list[float] = []
    for match in history:
        assert match.score is not None
        excluded: str | None = None
        if metric == "goals":
            goals_for, goals_against = match.score.goals(
                match.side(team_id), include_extra_time=sample_filter.period == "full"
            )
            value: float | None = {
                "for": goals_for,
                "against": goals_against,
                "total": goals_for + goals_against,
            }[perspective]
        else:
            own, opponent = match.stats_for(team_id)
            own_value, opponent_value = _stat_value(own, metric), _stat_value(opponent, metric)
            if perspective == "for":
                value = own_value
            elif perspective == "against":
                value = opponent_value
            else:
                value = None if own_value is None or opponent_value is None else own_value + opponent_value
            covers_extra_time = any(s is not None and s.includes_extra_time for s in (own, opponent))
            if value is None:
                excluded = "missing_stat"
            elif sample_filter.period == "regulation" and covers_extra_time:
                excluded = "stats_include_extra_time"
        if excluded is None and value is not None:
            used.append(float(value))
        items.append(_sample_item(match, team_id, value, excluded))

    warnings: list[str] = []
    if len(used) < SMALL_SAMPLE:
        warnings.append("SMALL_SAMPLE")
    if len(history) < sample_filter.window:
        warnings.append("SHORT_HISTORY")
    if any(item.excluded == "stats_include_extra_time" for item in items):
        warnings.append("EXCLUDED_EXTRA_TIME")
    if any(item.excluded == "missing_stat" for item in items):
        warnings.append("MISSING_STATS")
    return Average(
        team_id=team_id,
        metric=metric,
        perspective=perspective,
        sample_filter=sample_filter,
        value=round(sum(used) / len(used), 2) if used else None,
        n_used=len(used),
        n_considered=len(history),
        items=tuple(items),
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class LeagueReference:
    """Per-team, per-match league average shown next to every team number."""

    competition_id: str
    season: str
    value: float | None
    n_team_matches: int


def league_reference(
    matches: Iterable[Match],
    competition_id: str,
    season: str,
    metric: str,
    perspective: Perspective,
    before: datetime,
    period: Period = "regulation",
) -> LeagueReference:
    values: list[float] = []
    for match in matches:
        if match.competition_id != competition_id or match.season != season:
            continue
        if match.status != "finished" or match.score is None or match.kickoff >= before:
            continue
        for team_id in (match.home_id, match.away_id):
            if metric == "goals":
                goals_for, goals_against = match.score.goals(match.side(team_id), period == "full")
                value: float | None = {"for": goals_for, "against": goals_against, "total": goals_for + goals_against}[perspective]
            else:
                own, opponent = match.stats_for(team_id)
                if period == "regulation" and any(s is not None and s.includes_extra_time for s in (own, opponent)):
                    continue
                own_value, opponent_value = _stat_value(own, metric), _stat_value(opponent, metric)
                if perspective == "for":
                    value = own_value
                elif perspective == "against":
                    value = opponent_value
                else:
                    value = None if own_value is None or opponent_value is None else own_value + opponent_value
            if value is not None:
                values.append(float(value))
    return LeagueReference(
        competition_id=competition_id,
        season=season,
        value=round(sum(values) / len(values), 2) if values else None,
        n_team_matches=len(values),
    )


def form(
    matches: Iterable[Match],
    team_id: str,
    before: datetime,
    competitions: Mapping[str, Competition],
    sample_filter: SampleFilter = SampleFilter(window=5),
) -> FormSummary:
    """Recent results; points per game use 90-minute results (3/1/0)."""
    history = team_history(
        matches,
        team_id,
        before,
        competitions,
        venue=sample_filter.venue,
        competition_kinds=sample_filter.competition_kinds,
    )[: sample_filter.window]
    entries = []
    for match in history:
        assert match.score is not None
        side: Side = match.side(team_id)
        goals_for, goals_against = match.score.goals(side, include_extra_time=False)
        result_90 = _result(goals_for, goals_against)
        tie_winner = match.score.winner_of_tie()
        final_result: Result = "D" if tie_winner is None else ("W" if tie_winner == side else "L")
        decided_by = (
            "penalties" if match.score.shootout else "extra_time" if match.score.extra_time else "regulation"
        )
        entries.append(
            FormEntry(
                match_id=match.id,
                kickoff=match.kickoff,
                competition_id=match.competition_id,
                opponent_id=match.opponent(team_id),
                venue=match.venue_type(team_id),
                goals_for_90=goals_for,
                goals_against_90=goals_against,
                result_90=result_90,
                decided_by=decided_by,
                final_result=final_result,
            )
        )
    wins = sum(e.result_90 == "W" for e in entries)
    draws = sum(e.result_90 == "D" for e in entries)
    losses = sum(e.result_90 == "L" for e in entries)
    warnings = ["SMALL_SAMPLE"] if len(entries) < SMALL_SAMPLE else []
    return FormSummary(
        team_id=team_id,
        sample_filter=sample_filter,
        entries=tuple(entries),
        wins=wins,
        draws=draws,
        losses=losses,
        points_per_game=round((3 * wins + draws) / len(entries), 2) if entries else None,
        goals_for=sum(e.goals_for_90 for e in entries),
        goals_against=sum(e.goals_against_90 for e in entries),
        warnings=tuple(warnings),
    )


def coach_on(coaches: Iterable[CoachSpell], team_id: str, day: date) -> CoachSpell | None:
    for spell in coaches:
        if spell.team_id == team_id and spell.start <= day and (spell.end is None or day <= spell.end):
            return spell
    return None


def h2h(
    matches: Iterable[Match],
    team_a: str,
    team_b: str,
    before: datetime,
    coaches: Iterable[CoachSpell] = (),
    limit: int = 10,
) -> H2HSummary:
    """Head-to-head history from ``team_a``'s perspective, using 90-minute results."""
    meetings_all = sorted(
        (
            m
            for m in matches
            if m.involves(team_a)
            and m.involves(team_b)
            and m.status == "finished"
            and m.score is not None
            and m.kickoff < before
        ),
        key=lambda m: m.kickoff,
        reverse=True,
    )
    a_wins = draws = b_wins = a_goals = b_goals = 0
    for match in meetings_all:
        assert match.score is not None
        goals_a, goals_b = match.score.goals(match.side(team_a), include_extra_time=False)
        a_goals += goals_a
        b_goals += goals_b
        if goals_a > goals_b:
            a_wins += 1
        elif goals_a == goals_b:
            draws += 1
        else:
            b_wins += 1

    shown = tuple(
        H2HMeeting(
            match_id=m.id,
            kickoff=m.kickoff,
            competition_id=m.competition_id,
            home_id=m.home_id,
            away_id=m.away_id,
            venue=m.venue,
            neutral_venue=m.neutral_venue,
            score=m.score,  # type: ignore[arg-type]
            days_ago=local_days_between(m.kickoff, before),
        )
        for m in meetings_all[:limit]
    )
    last = shown[0] if shown else None
    changes: list[CoachChange] = []
    warnings: list[str] = []
    if last is None:
        warnings.append("H2H_NONE")
    else:
        last_day = last.kickoff.astimezone(LOCAL_TZ).date()
        today = before.astimezone(LOCAL_TZ).date()
        for spell in coaches:
            if spell.team_id in (team_a, team_b) and last_day < spell.start <= today:
                changes.append(CoachChange(team_id=spell.team_id, coach=spell.coach, start=spell.start))
        if last.days_ago > STALE_H2H_DAYS:
            warnings.append("H2H_STALE")
        if len(meetings_all) < 3:
            warnings.append("H2H_SMALL_SAMPLE")
        if changes:
            warnings.append("COACH_CHANGED_SINCE_LAST")
    return H2HSummary(
        team_a=team_a,
        team_b=team_b,
        meetings=shown,
        total_meetings=len(meetings_all),
        a_wins_90=a_wins,
        draws_90=draws,
        b_wins_90=b_wins,
        a_goals_90=a_goals,
        b_goals_90=b_goals,
        last_meeting=last,
        days_since_last=last.days_ago if last else None,
        coach_changes_since_last=tuple(sorted(changes, key=lambda c: c.start)),
        warnings=tuple(warnings),
    )


def _fixture_ref(match: Match, team_id: str, competitions: Mapping[str, Competition]) -> FixtureRef:
    return FixtureRef(
        match_id=match.id,
        kickoff=match.kickoff,
        competition_id=match.competition_id,
        competition_kind=_kind(competitions, match.competition_id),
        opponent_id=match.opponent(team_id),
        venue=match.venue_type(team_id),
        status=match.status,
        score=match.score,
        extra_time=bool(match.score and match.score.extra_time),
        shootout=bool(match.score and match.score.shootout),
    )


def schedule_context(
    matches: Sequence[Match],
    team_id: str,
    match: Match,
    competitions: Mapping[str, Competition],
) -> ScheduleContext:
    """Previous and next fixtures around ``match`` plus congestion flags."""
    history = team_history(matches, team_id, match.kickoff, competitions)
    previous = history[0] if history else None
    upcoming = sorted(
        (
            m
            for m in matches
            if m.involves(team_id) and m.kickoff > match.kickoff and m.status in ("scheduled", "postponed")
        ),
        key=lambda m: m.kickoff,
    )
    following = upcoming[0] if upcoming else None
    days_since = local_days_between(previous.kickoff, match.kickoff) if previous else None
    days_to = local_days_between(match.kickoff, following.kickoff) if following else None
    last_14 = sum(1 for m in history if local_days_between(m.kickoff, match.kickoff) <= 14)

    flags: list[str] = []
    if days_since is not None and days_since <= SHORT_REST_DAYS:
        flags.append("SHORT_REST")
    if previous is not None and days_since is not None and days_since <= NEAR_FIXTURE_DAYS:
        kind = _kind(competitions, previous.competition_id)
        if kind == "continental":
            flags.append("CONTINENTAL_BEFORE")
        elif kind == "domestic_cup":
            flags.append("CUP_BEFORE")
    if following is not None and days_to is not None and days_to <= NEAR_FIXTURE_DAYS:
        kind = _kind(competitions, following.competition_id)
        if kind == "continental":
            flags.append("CONTINENTAL_AFTER")
        elif kind == "domestic_cup":
            flags.append("CUP_AFTER")
    if previous is not None and previous.score is not None and previous.score.extra_time:
        flags.append("PREV_SHOOTOUT" if previous.score.shootout else "PREV_EXTRA_TIME")
    if last_14 >= 4:
        flags.append("CONGESTED")
    return ScheduleContext(
        team_id=team_id,
        previous=_fixture_ref(previous, team_id, competitions) if previous else None,
        next=_fixture_ref(following, team_id, competitions) if following else None,
        days_since_previous=days_since,
        days_to_next=days_to,
        matches_last_14_days=last_14,
        flags=tuple(flags),
    )


ROTATION_FLAGS = ("SHORT_REST", "CONTINENTAL_BEFORE", "CONTINENTAL_AFTER", "CUP_AFTER", "PREV_EXTRA_TIME", "PREV_SHOOTOUT", "CONGESTED")


def rotation_risk(context: ScheduleContext) -> tuple[Literal["low", "medium", "high"], tuple[str, ...]]:
    """Schedule-based heuristic only; it never claims knowledge of the lineup."""
    reasons = tuple(flag for flag in context.flags if flag in ROTATION_FLAGS)
    if len(reasons) >= 2:
        return "high", reasons
    return ("medium" if reasons else "low"), reasons


def standings(
    matches: Iterable[Match],
    competition_id: str,
    season: str,
    before: datetime,
    team_names: Mapping[str, str] | None = None,
) -> list[StandingRow]:
    """League table from finished matches before ``before`` (3/1/0, then GD, GF, name)."""
    table: dict[str, dict[str, int]] = {}

    def row(team_id: str) -> dict[str, int]:
        return table.setdefault(team_id, {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0})

    for match in matches:
        if match.competition_id != competition_id or match.season != season:
            continue
        row(match.home_id)
        row(match.away_id)
        if match.status != "finished" or match.score is None or match.kickoff >= before:
            continue
        for team_id in (match.home_id, match.away_id):
            goals_for, goals_against = match.score.goals(match.side(team_id), include_extra_time=False)
            entry = row(team_id)
            entry["p"] += 1
            entry["gf"] += goals_for
            entry["ga"] += goals_against
            result = _result(goals_for, goals_against)
            entry[{"W": "w", "D": "d", "L": "l"}[result]] += 1

    names = team_names or {}
    ordered = sorted(
        table.items(),
        key=lambda item: (
            -(3 * item[1]["w"] + item[1]["d"]),
            -(item[1]["gf"] - item[1]["ga"]),
            -item[1]["gf"],
            names.get(item[0], item[0]),
        ),
    )
    return [
        StandingRow(
            team_id=team_id,
            position=index + 1,
            played=entry["p"],
            won=entry["w"],
            drawn=entry["d"],
            lost=entry["l"],
            goals_for=entry["gf"],
            goals_against=entry["ga"],
            points=3 * entry["w"] + entry["d"],
        )
        for index, (team_id, entry) in enumerate(ordered)
    ]
