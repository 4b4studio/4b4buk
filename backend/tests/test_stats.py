from datetime import date, datetime, timedelta, timezone

import pytest

from buk.domain import CoachSpell, Competition, Match, Score, TeamMatchStats
from buk.stats import (
    SampleFilter,
    average,
    form,
    h2h,
    league_reference,
    rotation_risk,
    schedule_context,
    standings,
)

UTC = timezone.utc
REF = datetime(2026, 11, 14, 15, 0, tzinfo=UTC)
COMPS = {
    "lg": Competition("lg", "League", "league"),
    "cup": Competition("cup", "Cup", "domestic_cup"),
    "eu": Competition("eu", "Euro", "continental"),
}


def stats(corners=5, yellow=2, red=0, shots=12, on_target=4, et=False):
    return TeamMatchStats(corners, yellow, red, shots, on_target, includes_extra_time=et)


def match(mid, days_before, home, away, score, comp="lg", status="finished", neutral=False, hs=None, as_=None):
    return Match(
        id=mid,
        competition_id=comp,
        season="26",
        round=None,
        kickoff=REF - timedelta(days=days_before),
        home_id=home,
        away_id=away,
        venue="V",
        neutral_venue=neutral,
        status=status,
        score=score,
        home_stats=hs if hs is not None else (stats() if score else None),
        away_stats=as_ if as_ is not None else (stats(corners=3) if score else None),
    )


def test_average_uses_only_matches_before_reference_and_lists_sample():
    matches = [
        match("past1", 7, "a", "b", Score(2, 0)),
        match("past2", 14, "c", "a", Score(1, 1)),
        match("future", -3, "a", "d", Score(5, 0)),  # finished in the data but after the reference
    ]
    result = average(matches, "a", "goals", "for", REF, COMPS)
    assert [item.match_id for item in result.items] == ["past1", "past2"]
    assert result.value == 1.5
    assert result.n_used == 2 and "SMALL_SAMPLE" in result.warnings


def test_window_keeps_newest_matches_without_backfill():
    matches = [match(f"m{i}", i, "a", "b", Score(i % 3, 0)) for i in range(1, 13)]
    result = average(matches, "a", "goals", "for", REF, COMPS, SampleFilter(window=10))
    assert result.n_considered == 10
    assert result.items[0].match_id == "m1" and result.items[-1].match_id == "m10"


def test_extra_time_goals_only_in_full_period_and_penalties_never_count():
    cup_tie = match("tie", 3, "a", "b", Score(1, 1, 2, 1, None, None), comp="cup", hs=stats(et=True), as_=stats(et=True))
    shootout = match("pens", 10, "b", "a", Score(0, 0, 0, 0, 4, 5), comp="cup", hs=stats(et=True), as_=stats(et=True))
    regulation = average([cup_tie, shootout], "a", "goals", "for", REF, COMPS, SampleFilter(period="regulation"))
    full = average([cup_tie, shootout], "a", "goals", "for", REF, COMPS, SampleFilter(period="full"))
    assert regulation.value == 0.5  # 1 and 0 after 90 minutes
    assert full.value == 1.0  # 2 after extra time, 0 in the shoot-out tie


def test_stats_covering_extra_time_are_excluded_from_regulation_averages():
    normal = match("n", 7, "a", "b", Score(1, 0), hs=stats(corners=6))
    long = match("et", 3, "a", "b", Score(1, 1, 1, 2), comp="cup", hs=stats(corners=11, et=True), as_=stats(et=True))
    regulation = average([normal, long], "a", "corners", "for", REF, COMPS)
    full = average([normal, long], "a", "corners", "for", REF, COMPS, SampleFilter(period="full"))
    assert regulation.value == 6.0 and regulation.n_used == 1
    excluded = [i for i in regulation.items if i.excluded]
    assert excluded[0].match_id == "et" and excluded[0].excluded == "stats_include_extra_time"
    assert excluded[0].value == 11  # still shown to the user, struck through
    assert "EXCLUDED_EXTRA_TIME" in regulation.warnings
    assert full.value == 8.5 and full.n_used == 2


def test_missing_statistics_are_reported_not_hidden():
    with_stats = match("ok", 4, "a", "b", Score(1, 0), hs=stats(corners=4))
    without = Match("none", "lg", "26", None, REF - timedelta(days=8), "a", "b", "V", False, "finished", Score(0, 0))
    result = average([with_stats, without], "a", "corners", "for", REF, COMPS)
    assert result.value == 4.0 and result.n_used == 1 and result.n_considered == 2
    assert "MISSING_STATS" in result.warnings


def test_home_away_split_excludes_neutral_venues():
    matches = [
        match("home", 3, "a", "b", Score(2, 0)),
        match("away", 6, "b", "a", Score(0, 1)),
        match("final", 9, "a", "b", Score(3, 3), neutral=True),
    ]
    home = average(matches, "a", "goals", "for", REF, COMPS, SampleFilter(venue="home"))
    away = average(matches, "a", "goals", "for", REF, COMPS, SampleFilter(venue="away"))
    assert [i.match_id for i in home.items] == ["home"]
    assert [i.match_id for i in away.items] == ["away"]


def test_competition_filter():
    matches = [match("l", 3, "a", "b", Score(1, 0)), match("c", 6, "a", "b", Score(4, 0), comp="cup")]
    result = average(matches, "a", "goals", "for", REF, COMPS, SampleFilter(competition_kinds=("league",)))
    assert result.value == 1.0


def test_form_separates_ninety_minute_result_from_shootout_outcome():
    matches = [match("pens", 3, "b", "a", Score(1, 1, 1, 1, 3, 4), comp="cup"), match("win", 10, "a", "c", Score(2, 0))]
    summary = form(matches, "a", REF, COMPS, SampleFilter(window=5))
    first = summary.entries[0]
    assert first.result_90 == "D" and first.final_result == "W" and first.decided_by == "penalties"
    assert summary.points_per_game == 2.0  # (1 + 3) / 2 on 90-minute results


def test_h2h_perspective_staleness_and_coach_changes():
    matches = [
        match("old", 900, "b", "a", Score(2, 1)),
        match("older", 1200, "a", "b", Score(0, 0)),
    ]
    coaches = [CoachSpell("b", "New Coach", date(2026, 1, 1))]
    summary = h2h(matches, "a", "b", REF, coaches)
    assert summary.total_meetings == 2
    assert (summary.a_wins_90, summary.draws_90, summary.b_wins_90) == (0, 1, 1)
    assert summary.last_meeting is not None and summary.last_meeting.match_id == "old"
    assert summary.days_since_last == 900
    assert {"H2H_STALE", "H2H_SMALL_SAMPLE", "COACH_CHANGED_SINCE_LAST"} <= set(summary.warnings)
    assert summary.coach_changes_since_last[0].coach == "New Coach"


def test_h2h_without_meetings():
    summary = h2h([], "a", "b", REF)
    assert summary.last_meeting is None and summary.warnings == ("H2H_NONE",)


def test_schedule_context_flags_congestion_around_the_match():
    target = match("target", 0, "a", "b", None, status="scheduled")
    matches = [
        target,
        match("euro", 2, "a", "x", Score(1, 0), comp="eu"),
        match("cup", 6, "y", "a", Score(1, 1, 1, 1, 2, 4), comp="cup"),
        Match("next", "cup", "26", None, REF + timedelta(days=4), "a", "z", "V", False, "scheduled"),
    ]
    context = schedule_context(matches, "a", target, COMPS)
    assert context.previous is not None and context.previous.match_id == "euro"
    assert context.next is not None and context.next.match_id == "next"
    assert context.days_since_previous == 2 and context.days_to_next == 4
    assert {"SHORT_REST", "CONTINENTAL_BEFORE", "CUP_AFTER"} <= set(context.flags)
    level, reasons = rotation_risk(context)
    assert level == "high" and "CONTINENTAL_BEFORE" in reasons


def test_previous_shootout_is_flagged():
    target = match("target", 0, "a", "b", None, status="scheduled")
    previous = match("cup", 3, "y", "a", Score(0, 0, 0, 0, 2, 4), comp="cup")
    context = schedule_context([target, previous], "a", target, COMPS)
    assert "PREV_SHOOTOUT" in context.flags and "CUP_BEFORE" in context.flags


def test_standings_order_points_then_goal_difference():
    matches = [match("1", 10, "a", "b", Score(3, 0)), match("2", 9, "c", "d", Score(1, 0))]
    table = standings(matches, "lg", "26", REF)
    assert [row.team_id for row in table[:2]] == ["a", "c"]  # equal points, better goal difference
    assert table[0].points == 3 and table[0].goals_for == 3
    later = standings([*matches, match("3", 8, "b", "c", Score(0, 0))], "lg", "26", REF)
    assert later[0].team_id == "c" and later[0].points == 4


def test_league_reference_averages_all_team_matches():
    matches = [match("1", 10, "a", "b", Score(3, 1)), match("2", 9, "c", "d", Score(0, 0))]
    reference = league_reference(matches, "lg", "26", "goals", "for", REF)
    assert reference.value == 1.0 and reference.n_team_matches == 4


def test_unknown_metric_is_rejected():
    with pytest.raises(ValueError):
        average([], "a", "possession", "for", REF, COMPS)
