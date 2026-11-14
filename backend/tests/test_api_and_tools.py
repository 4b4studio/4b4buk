import pytest
from fastapi.testclient import TestClient

from buk.assistant import TOOL_SPECS, ToolError, run_tool
from buk.config import Settings
from buk.interest import Profile
from buk.main import create_app
from buk.providers.demo import DemoProvider

MATCH = "ld-2627-r13-npt-riv"


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app(settings=Settings()))


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_meta_declares_demo_data_and_missing_odds_source(client):
    body = client.get("/api/v1/meta").json()
    assert body["data"]["is_demo"] is True
    assert body["odds"]["status"] == "NO_ODDS_SOURCE"
    assert body["default_date"] == "2026-11-14"


def test_day_lists(client):
    body = client.get("/api/v1/matches", params={"date": "2026-11-14"}).json()
    ids = {m["id"] for m in body["matches"]}
    assert len(ids) == 11
    assert set(body["lists"]["watch"]) == ids == set(body["lists"]["analysis"])
    assert body["lists"]["odds"]["status"] == "NO_ODDS_SOURCE"


def test_empty_day(client):
    assert client.get("/api/v1/matches", params={"date": "2026-12-31"}).json()["matches"] == []


def test_match_detail_and_filters(client):
    body = client.get(f"/api/v1/matches/{MATCH}", params={"window": 5, "split": "context", "period": "full"}).json()
    assert body["window"] == 5 and body["split"] == "context" and body["period"] == "full"
    assert body["match"]["home"]["name"] == "Northport FC"
    assert all(row["home"]["n_considered"] <= 5 for row in body["metrics"])
    assert body["teams"]["riv"]["short_name"] == "RIV"


def test_match_detail_validation(client):
    assert client.get("/api/v1/matches/missing").status_code == 404
    assert client.get(f"/api/v1/matches/{MATCH}", params={"window": 99}).status_code == 422


def test_team_average_lists_matches_before_kickoff(client):
    body = client.get(
        "/api/v1/teams/npt/average",
        params={"match_id": MATCH, "metric": "corners", "perspective": "for", "venue": "home"},
    ).json()
    assert body["n_considered"] == len(body["items"])
    assert all(item["venue"] == "home" for item in body["items"])
    assert client.get("/api/v1/teams/xyz/average", params={"match_id": MATCH, "metric": "goals"}).status_code == 404


def test_assistant_tools_are_declared_without_model_calls(client):
    body = client.get("/api/v1/assistant/tools").json()
    assert body["model_calls"] == "disabled"
    assert {tool["name"] for tool in body["tools"]} == {spec["name"] for spec in TOOL_SPECS}


def test_tool_results_carry_provenance_and_sample_ids():
    dataset = DemoProvider().load()
    result = run_tool(
        dataset,
        Profile(),
        "team_average",
        {"team_id": "kes", "match_id": "ld-2627-r13-kes-ash", "metric": "corners", "perspective": "for"},
    )
    assert result["provenance"]["is_demo"] is True
    assert result["average"]["items"] and all(item["match_id"] for item in result["average"]["items"])
    with pytest.raises(ToolError):
        run_tool(dataset, Profile(), "team_average", {"team_id": "npt", "match_id": "ld-2627-r13-kes-ash", "metric": "goals"})
    with pytest.raises(ToolError):
        run_tool(dataset, Profile(), "unknown", {})
