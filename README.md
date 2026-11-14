# 4b4buk

Football-first match discovery and pre-match analysis. Open the app, ask "Co dziś
ciekawego?" and get three separately explained lists: matches to watch, matches
worth analysing, and (later) odds worth a look. The match page answers the usual
pre-match questions on one screen: form overall and home/away, averages of goals,
corners, cards and shots, head-to-head history, rest days, cup fixtures around the
match, absences and lineups. Every average opens into the exact matches behind it.

A 4b4apps product sold separately: it runs standalone at its own address with its own
icon and opens as a module from the owner's private 4b4 Hub and, later, from 4b4factory.
NBA, NHL and MLB are planned extensions, not v1.

> **Status: foundation.** The app runs on fictional demo data only. No real data
> provider, odds, accounts, notifications or AI model calls are connected.
> See [docs/STATUS.md](docs/STATUS.md).

## Quick start

Backend (Python 3.12+):

```sh
cd backend
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest -q
uvicorn buk.main:app --reload                  # http://127.0.0.1:8000/docs
```

Web app (Node 22.12+):

```sh
cd web
npm ci
npm run dev        # http://127.0.0.1:5173, proxies /api to the backend
npm run build      # type check + production build into web/dist
```

Single process serving the built PWA and the API:

```sh
cd backend
BUK_WEB_DIST=../web/dist uvicorn buk.main:app   # Windows: set BUK_WEB_DIST=..\web\dist
```

## Structure

| Path | Purpose |
| --- | --- |
| `backend/buk/domain.py` | Provider-neutral model; scores keep 90 min, extra time and penalties apart |
| `backend/buk/stats.py` | Deterministic statistics engine; every result carries its sample |
| `backend/buk/interest.py` | Rule-based watch and analysis lists with reason codes |
| `backend/buk/analysis.py` | Match-page bundle (comparisons, H2H, schedule, absences, data quality) |
| `backend/buk/assistant/tools.py` | Controlled tools for a future assistant; no model calls |
| `backend/buk/providers/` | Data-provider boundary and the demo provider |
| `backend/scripts/make_demo_data.py` | Deterministic generator of the fictional demo dataset |
| `web/` | React + Vite PWA (Polish UI) |
| `factory-module.json` | Proposed contract for opening 4b4buk from the 4b4 Hub and 4b4factory |
| `docs/` | Product, architecture, data sources, responsible use, decisions, status, roadmap |

## Documents

[Product](docs/PRODUCT.md) · [Architecture](docs/ARCHITECTURE.md) ·
[Data sources](docs/DATA_SOURCES.md) · [Responsible use](docs/RESPONSIBLE_USE.md) ·
[Decisions](docs/DECISIONS.md) · [Status](docs/STATUS.md) · [Roadmap](docs/ROADMAP.md) ·
[Agent rules](AGENTS.md)
