"""Match-detail bundle: one response that answers the core comparison questions.

The UI renders this bundle without computing statistics itself; filter changes
request a new bundle, so the UI and the assistant always share one engine.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from .domain import Absence, CoachSpell, Match, Side
from .interest import Interest, Profile, league_tables, score_match
from .providers.base import Dataset
from .stats import (
    COMPETITION_GROUPS,
    LOCAL_TZ,
    Average,
    FormSummary,
    H2HSummary,
    LeagueReference,
    Period,
    SampleFilter,
    ScheduleContext,
    StandingRow,
    average,
    coach_on,
    form,
    h2h,
    league_reference,
    rotation_risk,
    schedule_context,
)

Split = Literal["all", "context"]
CompetitionGroup = Literal["all", "league", "cups"]

METRIC_ROWS: tuple[tuple[str, str], ...] = (
    ("goals", "for"),
    ("goals", "against"),
    ("corners", "for"),
    ("corners", "against"),
    ("cards", "for"),
    ("shots", "for"),
    ("shots_on_target", "for"),
)


@dataclass(frozen=True)
class TeamRef:
    id: str
    name: str
    short_name: str


@dataclass(frozen=True)
class CompetitionRef:
    id: str
    name: str
    kind: str


@dataclass(frozen=True)
class MatchHeader:
    id: str
    kickoff: datetime
    competition: CompetitionRef
    round: str | None
    venue: str
    neutral_venue: bool
    status: str
    home: TeamRef
    away: TeamRef


@dataclass(frozen=True)
class MetricRow:
    metric: str
    perspective: str
    home: Average
    away: Average
    league: LeagueReference | None


@dataclass(frozen=True)
class FormThenNow:
    then: FormSummary | None
    now: FormSummary


@dataclass(frozen=True)
class TeamPanel:
    team: TeamRef
    side: Side
    sample_filter: SampleFilter
    form: FormSummary
    form_vs_last_h2h: FormThenNow
    schedule: ScheduleContext
    rotation_risk: str
    rotation_reasons: tuple[str, ...]
    coach: CoachSpell | None
    coach_days: int | None
    absences: tuple[Absence, ...]
    absences_status: Literal["reported", "none_reported", "no_data"]
    lineup_status: str
    lineup_updated_at: datetime | None
    table_position: int | None


@dataclass(frozen=True)
class DataInfo:
    source: str
    label: str
    as_of: datetime
    is_demo: bool


@dataclass(frozen=True)
class MatchBundle:
    match: MatchHeader
    split: Split
    competition_group: CompetitionGroup
    period: Period
    window: int
    home: TeamPanel
    away: TeamPanel
    metrics: tuple[MetricRow, ...]
    h2h: H2HSummary
    interest: Interest
    data_quality: tuple[str, ...]
    teams: dict[str, TeamRef]
    competitions: dict[str, CompetitionRef]
    data: DataInfo


def team_ref(dataset: Dataset, team_id: str) -> TeamRef:
    team = dataset.teams.get(team_id)
    if team is None:
        return TeamRef(id=team_id, name=team_id, short_name=team_id[:3].upper())
    return TeamRef(id=team.id, name=team.name, short_name=team.short_name)


def competition_ref(dataset: Dataset, competition_id: str) -> CompetitionRef:
    competition = dataset.competitions.get(competition_id)
    if competition is None:
        return CompetitionRef(id=competition_id, name=competition_id, kind="unknown")
    return CompetitionRef(id=competition.id, name=competition.name, kind=competition.kind)


def data_info(dataset: Dataset) -> DataInfo:
    return DataInfo(source=dataset.source, label=dataset.label, as_of=dataset.as_of, is_demo=dataset.is_demo)


def _panel(
    dataset: Dataset,
    match: Match,
    team_id: str,
    sample_filter: SampleFilter,
    history: H2HSummary,
    table: dict[str, StandingRow],
) -> TeamPanel:
    competitions = dataset.competitions
    recent = form(dataset.matches, team_id, match.kickoff, competitions, sample_filter)
    now5 = form(dataset.matches, team_id, match.kickoff, competitions, SampleFilter(window=5))
    then5 = (
        form(dataset.matches, team_id, history.last_meeting.kickoff, competitions, SampleFilter(window=5))
        if history.last_meeting
        else None
    )
    context = schedule_context(dataset.matches, team_id, match, competitions)
    risk, reasons = rotation_risk(context)
    match_day = match.kickoff.astimezone(LOCAL_TZ).date()
    coach = coach_on(dataset.coaches, team_id, match_day)
    absences = tuple(a for a in dataset.absences if a.team_id == team_id)
    if absences:
        absences_status: Literal["reported", "none_reported", "no_data"] = "reported"
    elif team_id in dataset.absence_coverage:
        absences_status = "none_reported"
    else:
        absences_status = "no_data"
    lineup = next((l for l in dataset.lineups if l.match_id == match.id and l.team_id == team_id), None)
    row = table.get(team_id)
    return TeamPanel(
        team=team_ref(dataset, team_id),
        side=match.side(team_id),
        sample_filter=sample_filter,
        form=recent,
        form_vs_last_h2h=FormThenNow(then=then5, now=now5),
        schedule=context,
        rotation_risk=risk,
        rotation_reasons=reasons,
        coach=coach,
        coach_days=(match_day - coach.start).days if coach else None,
        absences=absences,
        absences_status=absences_status,
        lineup_status=lineup.status if lineup else "not_available",
        lineup_updated_at=lineup.updated_at if lineup else None,
        table_position=row.position if row else None,
    )


def build_match_bundle(
    dataset: Dataset,
    match_id: str,
    profile: Profile,
    *,
    window: int = 10,
    split: Split = "all",
    period: Period = "regulation",
    competition_group: CompetitionGroup = "all",
) -> MatchBundle | None:
    match = dataset.match(match_id)
    if match is None:
        return None
    kinds = COMPETITION_GROUPS[competition_group]
    home_filter = SampleFilter(
        window=window, venue="home" if split == "context" else "all", competition_kinds=kinds, period=period
    )
    away_filter = SampleFilter(
        window=window, venue="away" if split == "context" else "all", competition_kinds=kinds, period=period
    )
    competitions = dataset.competitions
    history = h2h(dataset.matches, match.home_id, match.away_id, match.kickoff, dataset.coaches)
    tables = league_tables(dataset, [match], match.kickoff)
    table = {row.team_id: row for row in tables.get((match.competition_id, match.season), [])}

    home = _panel(dataset, match, match.home_id, home_filter, history, table)
    away = _panel(dataset, match, match.away_id, away_filter, history, table)
    is_league = competition_ref(dataset, match.competition_id).kind == "league"
    metrics = tuple(
        MetricRow(
            metric=metric,
            perspective=perspective,
            home=average(dataset.matches, match.home_id, metric, perspective, match.kickoff, competitions, home_filter),  # type: ignore[arg-type]
            away=average(dataset.matches, match.away_id, metric, perspective, match.kickoff, competitions, away_filter),  # type: ignore[arg-type]
            league=league_reference(dataset.matches, match.competition_id, match.season, metric, perspective, match.kickoff, period)  # type: ignore[arg-type]
            if is_league
            else None,
        )
        for metric, perspective in METRIC_ROWS
    )

    quality: list[str] = []
    if dataset.is_demo:
        quality.append("DEMO_DATA")
    if any("MISSING_STATS" in (row.home.warnings + row.away.warnings) for row in metrics):
        quality.append("MISSING_STATS")
    if any("EXCLUDED_EXTRA_TIME" in (row.home.warnings + row.away.warnings) for row in metrics):
        quality.append("EXCLUDED_EXTRA_TIME")
    if any("SMALL_SAMPLE" in (row.home.warnings + row.away.warnings) for row in metrics):
        quality.append("SMALL_SAMPLE")
    for panel in (home, away):
        if panel.absences_status == "no_data":
            quality.append("ABSENCES_NO_DATA")
        if panel.lineup_status != "confirmed":
            quality.append("LINEUPS_NOT_CONFIRMED")
    quality.extend(code for code in history.warnings if code not in quality)

    referenced = {match.home_id, match.away_id}
    for row in metrics:
        for result in (row.home, row.away):
            referenced.update(item.opponent_id for item in result.items)
    for panel in (home, away):
        referenced.update(entry.opponent_id for entry in panel.form.entries)
        for fixture in (panel.schedule.previous, panel.schedule.next):
            if fixture is not None:
                referenced.add(fixture.opponent_id)
    competition_ids = {match.competition_id}
    competition_ids.update(m.competition_id for m in history.meetings)
    for row in metrics:
        for result in (row.home, row.away):
            competition_ids.update(item.competition_id for item in result.items)
    for panel in (home, away):
        competition_ids.update(entry.competition_id for entry in panel.form.entries)
        for fixture in (panel.schedule.previous, panel.schedule.next):
            if fixture is not None:
                competition_ids.add(fixture.competition_id)

    return MatchBundle(
        match=MatchHeader(
            id=match.id,
            kickoff=match.kickoff,
            competition=competition_ref(dataset, match.competition_id),
            round=match.round,
            venue=match.venue,
            neutral_venue=match.neutral_venue,
            status=match.status,
            home=team_ref(dataset, match.home_id),
            away=team_ref(dataset, match.away_id),
        ),
        split=split,
        competition_group=competition_group,
        period=period,
        window=window,
        home=home,
        away=away,
        metrics=metrics,
        h2h=history,
        interest=score_match(dataset, match, profile, tables),
        data_quality=tuple(dict.fromkeys(quality)),
        teams={team_id: team_ref(dataset, team_id) for team_id in sorted(referenced)},
        competitions={cid: competition_ref(dataset, cid) for cid in sorted(competition_ids)},
        data=data_info(dataset),
    )
