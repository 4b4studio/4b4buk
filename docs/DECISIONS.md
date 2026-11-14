# 4b4buk Decisions

Statuses: APPROVED, WORKING_DIRECTION, PROPOSED, OPEN, SUPERSEDED. Studio-wide
decisions live in the hub (`4b4studio/studio`, `docs/DECISIONS.md`); this file records
4b4buk-specific ones and never overrides the hub.

## 2026-11-14 — Owner brief for 4b4buk (APPROVED requirements)

Source: the owner's research brief in the coordinating conversation. Football first;
NBA, NHL and MLB later but anticipated by the architecture. 4b4buk works as a module
opened from the 4b4 platform and standalone with its own address and icon, with the
same account, preferences and history in both. Code computes statistics; a model may
only use controlled tools and explain. Core comparisons must not require prompts.
No promises of sure wins; odds level, probability, data quality and expected value
stay separate.

## 2026-11-14 — Repository foundation (APPROVED request, PROPOSED content)

The owner asked to "prepare the repository and the application in our 4b4
infrastructure and build its foundation". The foundation is a runnable vertical slice
on fictional demo data: statistics engine with sample transparency, rule-based watch
and analysis lists, match bundle API, controlled assistant tools without model calls,
a Polish PWA and CI. It adds no paid service, credentials, hosting or publication.

## 2026-11-14 — Separate deployable integrated by contract (PROPOSED)

4b4buk needs its own server and database, while the hub's office/Factory interface
is planned as a static PWA without a server or accounts. Keep 4b4buk in its own
repository and deployment, integrated through `factory-module.json` (top-level
navigation, deep links) and a shared 4b4apps OpenID Connect identity once it exists.
Revisit when the hub settles the product-family structure.

## 2026-11-14 — Stack (PROPOSED, reversible)

Python/FastAPI backend with a deterministic statistics engine; PostgreSQL for storage
(next package); React + Vite + TypeScript PWA; one container for API and scheduled
worker. Rationale: Python suits statistics, ingestion and later modelling and matches
the hub's Python tooling; TypeScript suits a dense interactive UI. Alternatives
considered: full TypeScript (one language, weaker modelling) and server-rendered
Python with HTMX (simplest, weaker for rich comparisons).

## 2026-11-14 — PWA first (PROPOSED)

Ship v1 as an installable PWA; reconsider native apps only if the push-delivery
experiment fails on iOS. Store distribution is not planned for v1.

## 2026-11-14 — Odds disabled until gated (PROPOSED)

The odds list stays disabled until a licensed odds source with display rights, a
Polish legal review and a validated, logged probability model exist. No affiliate links
in v1. See `RESPONSIBLE_USE.md`.

## 2026-11-14 — Data provider shortlist (PROPOSED; purchase needs owner approval)

Sportmonks as the primary candidate, API-Football for the prototype and cross-checks,
validated by the 30-fixture experiment in `DATA_SOURCES.md` before any commitment.

## 2026-11-14 — Work-branch prefix and naming theme (OPEN)

Proposed prefix `bk` and theme "Football stadiums" (for example `work/bk-anfield`).
The owner chooses; registration in the hub's `tools/ai_team/projects.json` needs the
repository's numeric GitHub ID.
