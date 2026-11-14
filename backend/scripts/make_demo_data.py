#!/usr/bin/env python3
"""Generate the fictional demonstration dataset deterministically.

Every team, player, coach, venue and result is invented. The scenarios exist
to exercise the product's hard cases: a Thursday continental match before a
Saturday fixture, a midweek cup tie decided after extra time and penalties, a
stale head-to-head record, coach changes, a neutral-venue final, a foreign
away match without statistics, and predicted (not confirmed) lineups.

Usage: python scripts/make_demo_data.py [--check]
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 4
OUT = Path(__file__).resolve().parents[1] / "buk" / "demo" / "demo_data.json"
UTC = timezone.utc
AS_OF = datetime(2026, 11, 14, 8, 0, tzinfo=UTC)
SEASON = "2026/27"

LEAGUE, NORTH, CUP, EURO = "liga-demo", "liga-polnocna-demo", "puchar-demo", "euro-demo"
ID_CODES = {LEAGUE: "ld", NORTH: "lp", CUP: "pd", EURO: "ed"}
COMPETITIONS = [
    {"id": LEAGUE, "name": "Liga Demo", "kind": "league", "country": "Demolandia"},
    {"id": NORTH, "name": "Liga Północna Demo", "kind": "league", "country": "Nordfikcja"},
    {"id": CUP, "name": "Puchar Demolandii", "kind": "domestic_cup", "country": "Demolandia"},
    {"id": EURO, "name": "Euro Demo Cup", "kind": "continental", "country": None},
]

# id, name, short name, country, attack, defence (higher is better for both)
TEAMS = [
    ("npt", "Northport FC", "NPT", "Demolandia", 0.45, 0.35),
    ("riv", "Riverton United", "RIV", "Demolandia", 0.50, 0.40),
    ("kes", "Kestrel Athletic", "KES", "Demolandia", 0.25, 0.20),
    ("ash", "Ashford Town", "ASH", "Demolandia", 0.00, -0.05),
    ("mar", "Marlow City", "MAR", "Demolandia", 0.30, 0.15),
    ("gra", "Granite Rovers", "GRA", "Demolandia", 0.05, 0.05),
    ("bay", "Bayside Wanderers", "BAY", "Demolandia", -0.30, -0.25),
    ("hol", "Holloway Albion", "HOL", "Demolandia", 0.00, 0.00),
    ("elm", "Elmstead Rangers", "ELM", "Demolandia", -0.15, -0.10),
    ("cop", "Copperfield SC", "COP", "Demolandia", -0.25, -0.20),
    ("wes", "Westbrook Forest", "WES", "Demolandia", 0.10, -0.05),
    ("lin", "Lindale Harriers", "LIN", "Demolandia", 0.00, 0.05),
    ("sto", "Stonebridge Athletic", "STO", "Demolandia", -0.10, -0.10),
    ("fai", "Fairhaven Town", "FAI", "Demolandia", 0.05, 0.00),
    ("oak", "Oakmere United", "OAK", "Demolandia", 0.30, 0.20),
    ("tho", "Thornbury Rovers", "THO", "Demolandia", -0.30, -0.30),
    # Liga Północna Demo
    ("fjo", "Fjordby IF", "FJO", "Nordfikcja", 0.40, -0.15),
    ("ska", "Skarvik BK", "SKA", "Nordfikcja", 0.35, -0.10),
    ("nor", "Nordvik FK", "NOR", "Nordfikcja", 0.00, 0.20),
    ("ish", "Isholm SK", "ISH", "Nordfikcja", -0.20, -0.10),
    ("ber", "Bergstad IL", "BER", "Nordfikcja", 0.10, -0.20),
    ("lun", "Lunde FK", "LUN", "Nordfikcja", -0.10, 0.00),
    # Euro Demo Cup opponents
    ("spa", "Sporting Aurel", "SPA", "Aurelia", 0.35, 0.25),
    ("dyv", "Dynamo Velik", "DYV", "Velikia", 0.20, 0.30),
    ("kol", "Rapid Kolsk", "KOL", "Velikia", 0.00, 0.05),
    ("mon", "Real Montaro", "MON", "Aurelia", 0.40, 0.20),
    ("hel", "Helvar 1904", "HEL", "Helvaria", 0.10, 0.10),
    ("bra", "Bravia Union", "BRA", "Bravia", -0.05, 0.00),
    # lower-league cup sides
    ("sok", "Sokół Demo", "SOK", "Demolandia", -0.40, -0.30),
    ("orl", "Orlik Demo", "ORL", "Demolandia", -0.45, -0.35),
    ("jas", "Jastrząb Demo", "JAS", "Demolandia", -0.40, -0.35),
    ("zur", "Żuraw Demo", "ZUR", "Demolandia", -0.45, -0.40),
]
STRENGTH = {t[0]: (t[4], t[5]) for t in TEAMS}
NAMES = {t[0]: t[1] for t in TEAMS}
VENUES = {
    "npt": "Harbour Park",
    "riv": "Riverside Arena",
    "kes": "Kestrel Lane",
    "ash": "Mill Road",
    "mar": "Marlow Bowl",
    "gra": "Quarry Field",
    "oak": "Oakmere Stadium",
}
CORNER_STYLE = {"mar": 1.6, "npt": 0.6, "riv": 0.4, "oak": 0.5}
CORNER_CONCEDE = {"gra": 1.3, "bay": 0.8, "tho": 0.6}
CARD_STYLE = {"gra": 0.9, "bay": 0.6, "ash": 0.5, "kes": 0.3}

L1_IDS = [t[0] for t in TEAMS[:16]]
L2_IDS = [t[0] for t in TEAMS[16:22]]
L1_ROUND_DATES = ["2026-08-08", "2026-08-15", "2026-08-22", "2026-08-29", "2026-09-12", "2026-09-19",
                  "2026-09-26", "2026-10-03", "2026-10-17", "2026-10-24", "2026-10-31", "2026-11-07",
                  "2026-11-14", "2026-11-21", "2026-11-28"]
L1_TODAY = [("npt", "riv", "19:00"), ("kes", "ash", "14:00"), ("mar", "gra", "16:30"), ("oak", "wes", "14:00"),
            ("bay", "tho", "11:30"), ("hol", "lin", "14:00"), ("elm", "fai", "16:30"), ("cop", "sto", "11:30")]
L2_ROUND_DATES = ["2026-08-29", "2026-09-05", "2026-09-12", "2026-09-19", "2026-09-26", "2026-10-03",
                  "2026-10-10", "2026-10-17", "2026-10-24", "2026-10-31", "2026-11-14", "2026-11-21"]
L2_TODAY = [("fjo", "ska", "13:00"), ("nor", "ber", "15:00"), ("lun", "ish", "17:00")]
EURO_DATES = ["2026-09-17", "2026-10-01", "2026-10-22", "2026-11-12", "2026-11-26", "2026-12-10"]
EURO_GROUPS = [["npt", "spa", "dyv", "kol"], ["mar", "mon", "hel", "bra"]]


def poisson(rng: random.Random, lam: float) -> int:
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def when(day: str, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return datetime.fromisoformat(day).replace(hour=hour, minute=minute, tzinfo=UTC)


def iso(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def team_stats(rng: random.Random, team: str, opponent: str, home: bool, extra_time: bool) -> dict:
    attack, _ = STRENGTH[team]
    _, opp_defence = STRENGTH[opponent]
    edge = attack - opp_defence
    corners = poisson(rng, max(1.5, 4.6 + 2.0 * edge + (0.4 if home else 0) + CORNER_STYLE.get(team, 0) + CORNER_CONCEDE.get(opponent, 0)))
    shots = poisson(rng, max(4.0, 11.5 + 6.0 * edge + (1.0 if home else 0)))
    on_target = sum(1 for _ in range(shots) if rng.random() < 0.34)
    yellow = poisson(rng, 1.9 + CARD_STYLE.get(team, 0))
    red = 1 if rng.random() < 0.04 else 0
    if extra_time:  # provider totals cover 120 minutes
        corners += poisson(rng, 1.2)
        shots += poisson(rng, 3.0)
        yellow += poisson(rng, 0.5)
    return {"corners": corners, "yellow_cards": yellow, "red_cards": red, "shots": shots,
            "shots_on_target": min(on_target, shots), "includes_extra_time": extra_time}


def simulate_score(rng: random.Random, home: str, away: str, base: float, neutral: bool) -> tuple[int, int]:
    (h_att, h_def), (a_att, a_def) = STRENGTH[home], STRENGTH[away]
    advantage = 0.0 if neutral else 0.2
    return (poisson(rng, math.exp(base + advantage + h_att - a_def)),
            poisson(rng, math.exp(base + a_att - h_def)))


class Builder:
    def __init__(self) -> None:
        self.rng = random.Random(SEED)
        self.matches: list[dict] = []
        self.ids: set[str] = set()

    def add(self, *, competition: str, season: str, round_label: str, tag: str, kickoff: datetime, home: str,
            away: str, fixed: dict | None = None, base: float = math.log(1.25), neutral_venue: str | None = None,
            stats: bool = True) -> dict:
        match_id = f"{ID_CODES[competition]}-{season[2:4]}{season[5:7]}-{tag}-{home}-{away}"
        if match_id in self.ids:
            raise ValueError(f"duplicate match id {match_id}")
        self.ids.add(match_id)
        finished = kickoff < AS_OF
        record = {
            "id": match_id, "competition_id": competition, "season": season, "round": round_label,
            "kickoff": iso(kickoff), "home_id": home, "away_id": away,
            "venue": neutral_venue or VENUES.get(home, f"{NAMES[home]} Ground"),
            "neutral_venue": neutral_venue is not None,
            "status": "finished" if finished else "scheduled",
            "score": None, "home_stats": None, "away_stats": None,
        }
        if finished:
            if fixed is None:
                h, a = simulate_score(self.rng, home, away, base, neutral_venue is not None)
                score = {"home_90": h, "away_90": a}
            else:
                score = dict(fixed)
            extra_time = "home_aet" in score
            record["score"] = score
            if stats:
                record["home_stats"] = team_stats(self.rng, home, away, neutral_venue is None, extra_time)
                record["away_stats"] = team_stats(self.rng, away, home, False, extra_time)
        self.matches.append(record)
        return record


def circle_rounds(team_count: int) -> list[list[tuple[int, int]]]:
    positions = list(range(team_count))
    rounds = []
    for number in range(team_count - 1):
        pairs = []
        for i in range(team_count // 2):
            a, b = positions[i], positions[team_count - 1 - i]
            pairs.append((a, b) if (number + i) % 2 == 0 else (b, a))
        rounds.append(pairs)
        positions = [positions[0], positions[-1], *positions[1:-1]]
    return rounds


def assign(rounds: list[list[tuple[int, int]]], round_index: int, wanted: list[tuple[str, str, str]]) -> dict[int, str]:
    """Map schedule positions to team ids so ``round_index`` contains ``wanted``."""
    mapping: dict[int, str] = {}
    for (home_pos, away_pos), (home, away, _) in zip(rounds[round_index], wanted):
        mapping[home_pos], mapping[away_pos] = home, away
    return mapping


def build_league(builder: Builder, competition: str, team_ids: list[str], dates: list[str],
                 today_round: int, wanted: list[tuple[str, str, str]], base: float) -> None:
    single = circle_rounds(len(team_ids))
    schedule = single + [[(b, a) for a, b in rnd] for rnd in single]
    schedule = (schedule * 2)[: len(dates)]
    mapping = assign(schedule, today_round - 1, wanted)
    times = {frozenset((h, a)): t for h, a, t in wanted}
    slots = ["11:30", "14:00", "14:00", "16:30", "16:30", "19:00", "13:00", "15:00"]
    for number, (rnd, day) in enumerate(zip(schedule, dates), start=1):
        for index, (home_pos, away_pos) in enumerate(rnd):
            home, away = mapping[home_pos], mapping[away_pos]
            if number == today_round:
                home, away = next((h, a) for h, a, _ in wanted if {h, a} == {home, away})
            kickoff = when(day, times.get(frozenset((home, away)), slots[index % len(slots)]) if number == today_round else slots[index % len(slots)])
            builder.add(competition=competition, season=SEASON, round_label=f"{number}. kolejka",
                        tag=f"r{number}", kickoff=kickoff, home=home, away=away, base=base)


def fixed(h90: int, a90: int, aet: tuple[int, int] | None = None, pens: tuple[int, int] | None = None) -> dict:
    score: dict = {"home_90": h90, "away_90": a90}
    if aet:
        score.update(home_aet=aet[0], away_aet=aet[1])
    if pens:
        score.update(home_pens=pens[0], away_pens=pens[1])
    return score


def build_cup(builder: Builder) -> None:
    r1 = [("kes", "bay", fixed(3, 1)), ("elm", "mar", fixed(1, 1, (1, 2))), ("ash", "riv", fixed(0, 2)),
          ("hol", "gra", fixed(2, 2, (2, 2), (4, 5))), ("cop", "npt", fixed(0, 1)), ("tho", "oak", fixed(1, 3)),
          ("lin", "wes", fixed(1, 1, (1, 1), (3, 4))), ("sto", "fai", fixed(0, 2))]
    for home, away, score in r1:
        builder.add(competition=CUP, season=SEASON, round_label="1/16 finału", tag="r1", kickoff=when("2026-09-23", "18:00"),
                    home=home, away=away, fixed=score)
    r2 = [("kes", "npt", fixed(2, 1)), ("oak", "mar", fixed(0, 1)), ("gra", "riv", fixed(1, 1, (1, 2))),
          ("fai", "wes", fixed(2, 2, (2, 2), (5, 3)))]
    for home, away, score in r2:
        builder.add(competition=CUP, season=SEASON, round_label="1/8 finału", tag="r2", kickoff=when("2026-10-28", "18:30"),
                    home=home, away=away, fixed=score)
    builder.add(competition=CUP, season=SEASON, round_label="ćwierćfinał", tag="qf", kickoff=when("2026-11-11", "18:00"),
                home="sok", away="kes", fixed=fixed(1, 1, (1, 1), (4, 5)))
    builder.add(competition=CUP, season=SEASON, round_label="ćwierćfinał", tag="qf", kickoff=when("2026-11-11", "18:00"),
                home="orl", away="fai", fixed=fixed(0, 3))
    builder.add(competition=CUP, season=SEASON, round_label="ćwierćfinał", tag="qf", kickoff=when("2026-11-18", "18:30"),
                home="jas", away="mar")
    builder.add(competition=CUP, season=SEASON, round_label="ćwierćfinał", tag="qf", kickoff=when("2026-11-18", "19:30"),
                home="zur", away="riv")


def build_euro(builder: Builder) -> None:
    pattern = [[(0, 1), (2, 3)], [(3, 0), (1, 2)], [(0, 2), (3, 1)], [(1, 0), (3, 2)], [(0, 3), (2, 1)], [(2, 0), (1, 3)]]
    for number, (day, pairs) in enumerate(zip(EURO_DATES, pattern), start=1):
        for group in EURO_GROUPS:
            for home_pos, away_pos in pairs:
                home, away = group[home_pos], group[away_pos]
                # A foreign away fixture whose statistics the source never delivered.
                no_stats = home == "kol" and away == "npt"
                builder.add(competition=EURO, season=SEASON, round_label=f"{number}. kolejka grupy",
                            tag=f"md{number}", kickoff=when(day, "18:45" if group[0] == "npt" else "20:00"), home=home, away=away,
                            stats=not no_stats)


def build_history(builder: Builder) -> None:
    featured = [
        (LEAGUE, "2025/26", "2026-04-18", "npt", "riv", fixed(2, 2), None),
        (LEAGUE, "2025/26", "2025-11-29", "riv", "npt", fixed(1, 0), None),
        (CUP, "2024/25", "2025-05-24", "npt", "riv", fixed(1, 1, (1, 1), (3, 4)), "Stadion Narodowy Demo"),
        (LEAGUE, "2024/25", "2025-03-08", "npt", "riv", fixed(3, 1), None),
        (LEAGUE, "2024/25", "2024-10-05", "riv", "npt", fixed(0, 0), None),
        (LEAGUE, "2023/24", "2024-04-13", "riv", "npt", fixed(2, 1), None),
        (LEAGUE, "2023/24", "2023-11-25", "npt", "riv", fixed(1, 2), None),
        (LEAGUE, "2022/23", "2023-02-11", "kes", "ash", fixed(2, 0), None),
        (LEAGUE, "2022/23", "2022-09-03", "ash", "kes", fixed(1, 1), None),
        (LEAGUE, "2025/26", "2026-03-14", "gra", "mar", fixed(0, 2), None),
        (LEAGUE, "2025/26", "2025-10-04", "mar", "gra", fixed(3, 1), None),
        (LEAGUE, "2024/25", "2025-02-22", "mar", "gra", fixed(1, 1), None),
        (LEAGUE, "2024/25", "2024-09-21", "gra", "mar", fixed(2, 1), None),
    ]
    for competition, season, day, home, away, score, neutral in featured:
        round_label = "finał" if neutral else "liga"
        builder.add(competition=competition, season=season, round_label=round_label, tag=day.replace("-", ""),
                    kickoff=when(day, "15:00"), home=home, away=away, fixed=score, neutral_venue=neutral)
    pairs = [("oak", "wes"), ("bay", "tho"), ("hol", "lin"), ("elm", "fai"), ("cop", "sto")]
    seasons = [("2025/26", "2026-02-"), ("2025/26", "2025-09-"), ("2024/25", "2025-04-"), ("2023/24", "2023-12-")]
    for first, second in pairs:
        for index, (season, prefix) in enumerate(seasons[: 2 + builder.rng.randrange(3)]):
            home, away = (first, second) if index % 2 == 0 else (second, first)
            day = f"{prefix}{10 + builder.rng.randrange(15):02d}"
            builder.add(competition=LEAGUE, season=season, round_label="liga", tag=day.replace("-", ""),
                        kickoff=when(day, "15:00"), home=home, away=away)


COACHES = [
    ("npt", "Adam Rok", "2023-07-01", None),
    ("riv", "Ivo Brandl", "2022-07-01", "2025-01-09"), ("riv", "Leo Hart", "2025-01-10", None),
    ("kes", "Olek Mróz", "2021-07-01", "2025-05-31"), ("kes", "Ewa Lind", "2025-06-01", None),
    ("ash", "Piotr Nowik", "2024-07-01", "2026-10-19"), ("ash", "Marek Zawada", "2026-10-20", None),
    ("mar", "Iga Sowa", "2024-07-01", None),
    ("gra", "Tom Reyes", "2023-07-01", "2026-08-19"), ("gra", "Bruno Kos", "2026-08-20", None),
    ("oak", "Nils Berg", "2024-01-05", None),
]
ABSENCES = [
    ("npt", "K. Brandt", "injury", "confirmed", "key", "club_statement"),
    ("npt", "M. Ilić", "suspension", "confirmed", "regular", "competition_suspensions"),
    ("npt", "D. Osei", "injury", "doubtful", "key", "press_conference"),
    ("riv", "S. Duarte", "injury", "confirmed", "regular", "club_statement"),
    ("kes", "P. Varga", "other", "doubtful", "key", "press_conference"),
    ("ash", "R. Moyo", "suspension", "confirmed", "key", "competition_suspensions"),
    ("mar", "T. Hale", "injury", "confirmed", "key", "club_statement"),
    ("mar", "J. Brook", "injury", "doubtful", "regular", "press_conference"),
]
ABSENCE_COVERAGE = ["npt", "riv", "kes", "ash", "mar", "oak", "wes", "hol", "lin"]


def build() -> dict:
    builder = Builder()
    build_league(builder, LEAGUE, L1_IDS, L1_ROUND_DATES, 13, L1_TODAY, math.log(1.25))
    build_league(builder, NORTH, L2_IDS, L2_ROUND_DATES, 11, L2_TODAY, math.log(1.55))
    build_cup(builder)
    build_euro(builder)
    build_history(builder)
    today_npt_riv = next(m["id"] for m in builder.matches if m["kickoff"].startswith("2026-11-14") and m["home_id"] == "npt")
    lineups = [
        {"match_id": today_npt_riv, "team_id": team, "status": "predicted", "updated_at": "2026-11-14T07:00:00Z"}
        for team in ("npt", "riv")
    ]
    builder.matches.sort(key=lambda m: (m["kickoff"], m["id"]))
    return {
        "meta": {
            "label": "DEMO — fictional teams, players, coaches and results",
            "demo": True,
            "as_of": iso(AS_OF),
            "generator": "backend/scripts/make_demo_data.py",
            "seed": SEED,
            "default_profile": {"followed_teams": ["npt"], "followed_competitions": [LEAGUE]},
            "absence_coverage": ABSENCE_COVERAGE,
        },
        "competitions": COMPETITIONS,
        "teams": [{"id": t[0], "name": t[1], "short_name": t[2], "country": t[3]} for t in TEAMS],
        "matches": builder.matches,
        "coaches": [{"team_id": t, "coach": c, "start": s, "end": e} for t, c, s, e in COACHES],
        "absences": [
            {"team_id": t, "player": p, "reason": r, "status": st, "importance": imp, "source": src,
             "updated_at": "2026-11-14T07:30:00Z"}
            for t, p, r, st, imp, src in ABSENCES
        ],
        "lineups": lineups,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the committed file is stale")
    args = parser.parse_args()
    text = json.dumps(build(), ensure_ascii=False, indent=1) + "\n"
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != text:
            print("demo_data.json is stale; run scripts/make_demo_data.py", file=sys.stderr)
            return 1
        print("demo_data.json is up to date")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
