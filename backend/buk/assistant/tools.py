"""Controlled tools for the analytical assistant.

The language model never computes statistics. It selects a tool, supplies
parameters, and explains the returned JSON. Every result carries provenance:
data source, timestamp, and the IDs of the matches behind each number. The
foundation defines and tests the tools but calls no model; a provider adapter
is a separate, owner-approved package because it has running costs.

``input_schema`` is plain JSON Schema, usable by any tool-calling LLM API.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from ..analysis import build_match_bundle, data_info
from ..interest import Profile, ordered_ids, rank_day
from ..providers.base import Dataset
from ..serialize import jsonable
from ..stats import COMPETITION_GROUPS, METRICS, SampleFilter, average, h2h, schedule_context

_FILTER_PROPERTIES: dict[str, Any] = {
    "window": {"type": "integer", "minimum": 3, "maximum": 20, "default": 10},
    "period": {"type": "string", "enum": ["regulation", "full"], "default": "regulation"},
    "competitions": {"type": "string", "enum": ["all", "league", "cups"], "default": "all"},
}

TOOL_SPECS: list[dict[str, Any]] = [
    {
        "name": "list_matches",
        "description": "Matches on a Europe/Warsaw calendar date with watch/analysis scores and reason codes.",
        "input_schema": {
            "type": "object",
            "properties": {"date": {"type": "string", "format": "date"}},
            "required": ["date"],
        },
    },
    {
        "name": "match_bundle",
        "description": "Full comparison for one match: form, averages with samples, H2H, schedule, absences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "match_id": {"type": "string"},
                "split": {"type": "string", "enum": ["all", "context"], "default": "all"},
                **_FILTER_PROPERTIES,
            },
            "required": ["match_id"],
        },
    },
    {
        "name": "team_average",
        "description": "Average of one metric for one team before a match, with every match used or excluded.",
        "input_schema": {
            "type": "object",
            "properties": {
                "team_id": {"type": "string"},
                "match_id": {"type": "string", "description": "Reference match; only earlier matches count."},
                "metric": {"type": "string", "enum": list(METRICS)},
                "perspective": {"type": "string", "enum": ["for", "against", "total"]},
                "venue": {"type": "string", "enum": ["all", "home", "away"], "default": "all"},
                **_FILTER_PROPERTIES,
            },
            "required": ["team_id", "match_id", "metric", "perspective"],
        },
    },
    {
        "name": "head_to_head",
        "description": "Meetings between two teams before a match, newest first, using 90-minute results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "match_id": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 10},
            },
            "required": ["match_id"],
        },
    },
    {
        "name": "schedule_context",
        "description": "Previous and next fixture, rest days and congestion flags for one team around a match.",
        "input_schema": {
            "type": "object",
            "properties": {"team_id": {"type": "string"}, "match_id": {"type": "string"}},
            "required": ["team_id", "match_id"],
        },
    },
]


class ToolError(ValueError):
    """Invalid tool call; the message is safe to return to the model."""


def _match(dataset: Dataset, match_id: str):
    match = dataset.match(match_id)
    if match is None:
        raise ToolError(f"unknown match_id: {match_id}")
    return match


def run_tool(dataset: Dataset, profile: Profile, name: str, args: dict[str, Any]) -> dict[str, Any]:
    provenance = jsonable(data_info(dataset))
    if name == "list_matches":
        try:
            day = date.fromisoformat(str(args["date"]))
        except (KeyError, ValueError) as exc:
            raise ToolError("date must be YYYY-MM-DD") from exc
        matches, scores = rank_day(dataset, day, profile)
        return {
            "provenance": provenance,
            "watch_order": ordered_ids(matches, scores, "watch"),
            "analysis_order": ordered_ids(matches, scores, "analysis"),
            "odds": {"status": "NO_ODDS_SOURCE"},
            "matches": [jsonable(scores[m.id]) | {"kickoff": jsonable(m.kickoff), "home_id": m.home_id, "away_id": m.away_id} for m in matches],
        }
    if name == "match_bundle":
        _match(dataset, str(args.get("match_id")))
        bundle = build_match_bundle(
            dataset,
            str(args["match_id"]),
            profile,
            window=int(args.get("window", 10)),
            split=args.get("split", "all"),
            period=args.get("period", "regulation"),
            competition_group=args.get("competitions", "all"),
        )
        return {"provenance": provenance, "bundle": jsonable(bundle)}
    if name == "team_average":
        match = _match(dataset, str(args.get("match_id")))
        team_id = str(args.get("team_id"))
        if team_id not in (match.home_id, match.away_id):
            raise ToolError("team_id must be one of the match's teams")
        if args.get("metric") not in METRICS:
            raise ToolError(f"metric must be one of {', '.join(METRICS)}")
        sample_filter = SampleFilter(
            window=int(args.get("window", 10)),
            venue=args.get("venue", "all"),
            competition_kinds=COMPETITION_GROUPS[args.get("competitions", "all")],
            period=args.get("period", "regulation"),
        )
        result = average(
            dataset.matches,
            team_id,
            args["metric"],
            args.get("perspective", "for"),
            match.kickoff,
            dataset.competitions,
            sample_filter,
        )
        return {"provenance": provenance, "average": jsonable(result)}
    if name == "head_to_head":
        match = _match(dataset, str(args.get("match_id")))
        result = h2h(dataset.matches, match.home_id, match.away_id, match.kickoff, dataset.coaches, int(args.get("limit", 10)))
        return {"provenance": provenance, "head_to_head": jsonable(result)}
    if name == "schedule_context":
        match = _match(dataset, str(args.get("match_id")))
        team_id = str(args.get("team_id"))
        if team_id not in (match.home_id, match.away_id):
            raise ToolError("team_id must be one of the match's teams")
        result = schedule_context(dataset.matches, team_id, match, dataset.competitions)
        return {"provenance": provenance, "schedule": jsonable(result)}
    raise ToolError(f"unknown tool: {name}")
