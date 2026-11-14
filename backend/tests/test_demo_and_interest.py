import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from buk.analysis import build_match_bundle
from buk.interest import Profile, ordered_ids, rank_day
from buk.providers.demo import DemoProvider

BACKEND = Path(__file__).resolve().parents[1]
DAY = date(2026, 11, 14)
FOLLOW = Profile(followed_teams=frozenset({"npt"}), followed_competitions=frozenset({"liga-demo"}))


@pytest.fixture(scope="module")
def dataset():
    return DemoProvider().load()


def test_committed_demo_file_matches_generator():
    result = subprocess.run(
        [sys.executable, "scripts/make_demo_data.py", "--check"], cwd=BACKEND, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_demo_dataset_is_labelled_and_consistent(dataset):
    assert dataset.is_demo and "DEMO" in dataset.label
    ids = [m.id for m in dataset.matches]
    assert len(ids) == len(set(ids))
    for m in dataset.matches:
        assert m.home_id in dataset.teams and m.away_id in dataset.teams
        assert (m.status == "finished") == (m.kickoff < dataset.as_of)


def test_followed_top_clash_leads_the_watch_list(dataset):
    matches, scores = rank_day(dataset, DAY, FOLLOW)
    watch = ordered_ids(matches, scores, "watch")
    assert watch[0] == "ld-2627-r13-npt-riv"
    codes = {r.code for r in scores[watch[0]].watch.reasons}
    assert {"FOLLOWED_TEAM", "TOP_CLASH"} <= codes


def test_analysis_list_explains_schedule_and_history_signals(dataset):
    matches, scores = rank_day(dataset, DAY, FOLLOW)
    interest = scores["ld-2627-r13-kes-ash"]
    reasons = {(r.code, r.params.get("team")) for r in interest.analysis.reasons}
    assert ("PREV_SHOOTOUT", "kes") in reasons and ("NEW_COACH", "ash") in reasons
    assert {"H2H_STALE", "COACH_CHANGED_SINCE_LAST"} <= {w.code for w in interest.warnings}


def test_exactly_one_discovery_outside_followed_interests(dataset):
    matches, scores = rank_day(dataset, DAY, FOLLOW)
    discoveries = [s for s in scores.values() if s.discovery]
    assert len(discoveries) == 1 and not discoveries[0].followed


def test_personalisation_changes_watch_scores_only(dataset):
    _, followed = rank_day(dataset, DAY, FOLLOW)
    _, neutral = rank_day(dataset, DAY, Profile())
    for match_id in followed:
        assert followed[match_id].analysis == neutral[match_id].analysis


def test_bundle_exposes_samples_and_quality_flags(dataset):
    bundle = build_match_bundle(dataset, "ld-2627-r13-npt-riv", FOLLOW)
    assert bundle is not None
    for row in bundle.metrics:
        for result in (row.home, row.away):
            assert result.n_used <= result.n_considered <= 10
            assert all(item.kickoff < bundle.match.kickoff for item in result.items)
        assert row.league is not None and row.league.value is not None
    assert "DEMO_DATA" in bundle.data_quality
    assert "MISSING_STATS" in bundle.data_quality  # the foreign away match without statistics
    assert bundle.home.rotation_risk == "high"
    assert bundle.h2h.last_meeting is not None and bundle.h2h.total_meetings == 7
    assert bundle.home.form_vs_last_h2h.then is not None


def test_context_split_uses_home_and_away_matches(dataset):
    bundle = build_match_bundle(dataset, "ld-2627-r13-npt-riv", FOLLOW, split="context")
    assert bundle is not None
    goals = bundle.metrics[0]
    assert all(item.venue == "home" for item in goals.home.items)
    assert all(item.venue == "away" for item in goals.away.items)


def test_unknown_match_returns_none(dataset):
    assert build_match_bundle(dataset, "missing", FOLLOW) is None
