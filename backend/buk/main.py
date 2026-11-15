"""HTTP API and optional static hosting of the built PWA.

Run locally:  uvicorn buk.main:app --reload
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .analysis import build_match_bundle, competition_ref, data_info, team_ref
from .assistant import TOOL_SPECS
from .config import Settings, load_settings
from .interest import Profile, ordered_ids, rank_day
from .providers.base import Dataset
from .providers.demo import DemoProvider
from .serialize import jsonable
from .stats import COMPETITION_GROUPS, METRICS, LOCAL_TZ, SampleFilter, average


def _load_dataset(settings: Settings) -> Dataset:
    if settings.data_source != "demo":
        raise RuntimeError(f"unsupported data source: {settings.data_source}")
    return DemoProvider().load()


def _profile(dataset: Dataset, teams: list[str], competitions: list[str]) -> Profile:
    if not teams and not competitions:
        teams = dataset.default_profile.get("followed_teams", [])
        competitions = dataset.default_profile.get("followed_competitions", [])
    return Profile(followed_teams=frozenset(teams), followed_competitions=frozenset(competitions))


def create_app(dataset: Dataset | None = None, settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    data = dataset or _load_dataset(settings)
    app = FastAPI(title="4b4buk API", version=__version__)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/v1/meta")
    def meta() -> JSONResponse:
        return JSONResponse(
            {
                "version": __version__,
                "data": jsonable(data_info(data)),
                "default_profile": data.default_profile,
                "default_date": data.as_of.astimezone(LOCAL_TZ).date().isoformat(),
                "odds": {"status": "NO_ODDS_SOURCE"},
                "metrics": list(METRICS),
            }
        )

    @app.get("/api/v1/matches")
    def list_matches(
        day: date | None = Query(default=None, alias="date"),
        follow_team: list[str] = Query(default=[]),
        follow_competition: list[str] = Query(default=[]),
    ) -> JSONResponse:
        selected_day = day or data.as_of.astimezone(LOCAL_TZ).date()
        profile = _profile(data, follow_team, follow_competition)
        matches, scores = rank_day(data, selected_day, profile)
        items = []
        for match in matches:
            items.append(
                {
                    "id": match.id,
                    "kickoff": jsonable(match.kickoff),
                    "status": match.status,
                    "round": match.round,
                    "competition": jsonable(competition_ref(data, match.competition_id)),
                    "home": jsonable(team_ref(data, match.home_id)),
                    "away": jsonable(team_ref(data, match.away_id)),
                    "interest": jsonable(scores[match.id]),
                }
            )
        return JSONResponse(
            {
                "date": selected_day.isoformat(),
                "data": jsonable(data_info(data)),
                "profile": jsonable(profile),
                "matches": items,
                "lists": {
                    "watch": ordered_ids(matches, scores, "watch"),
                    "analysis": ordered_ids(matches, scores, "analysis"),
                    "odds": {"status": "NO_ODDS_SOURCE", "items": []},
                },
            }
        )

    @app.get("/api/v1/matches/{match_id}")
    def match_detail(
        match_id: str,
        window: int = Query(default=10, ge=3, le=20),
        split: Literal["all", "context"] = "all",
        period: Literal["regulation", "full"] = "regulation",
        competitions: Literal["all", "league", "cups"] = "all",
        follow_team: list[str] = Query(default=[]),
        follow_competition: list[str] = Query(default=[]),
    ) -> JSONResponse:
        bundle = build_match_bundle(
            data,
            match_id,
            _profile(data, follow_team, follow_competition),
            window=window,
            split=split,
            period=period,
            competition_group=competitions,
        )
        if bundle is None:
            raise HTTPException(status_code=404, detail="match not found")
        return JSONResponse(jsonable(bundle))

    @app.get("/api/v1/teams/{team_id}/average")
    def team_average(
        team_id: str,
        match_id: str,
        metric: Literal["goals", "corners", "cards", "yellow_cards", "red_cards", "shots", "shots_on_target"],
        perspective: Literal["for", "against", "total"] = "for",
        venue: Literal["all", "home", "away"] = "all",
        window: int = Query(default=10, ge=3, le=20),
        period: Literal["regulation", "full"] = "regulation",
        competitions: Literal["all", "league", "cups"] = "all",
    ) -> JSONResponse:
        match = data.match(match_id)
        if match is None or team_id not in (match.home_id, match.away_id):
            raise HTTPException(status_code=404, detail="match or team not found")
        result = average(
            data.matches,
            team_id,
            metric,
            perspective,
            match.kickoff,
            data.competitions,
            SampleFilter(window=window, venue=venue, competition_kinds=COMPETITION_GROUPS[competitions], period=period),
        )
        return JSONResponse(jsonable(result))

    @app.get("/api/v1/assistant/tools")
    def assistant_tools() -> JSONResponse:
        return JSONResponse({"model_calls": "disabled", "tools": TOOL_SPECS})

    web_dist = settings.web_dist
    if web_dist is not None and (web_dist / "index.html").is_file():
        index = web_dist / "index.html"

        @app.get("/{path:path}", include_in_schema=False)
        def spa(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(status_code=404)
            candidate = (web_dist / path).resolve()
            if path and candidate.is_file() and candidate.is_relative_to(web_dist):
                return FileResponse(candidate)
            return FileResponse(index)

    return app


app = create_app()
