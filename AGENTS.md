# 4b4buk — Agent Instructions

Applies to ChatGPT, Codex, Claude and other assistants working in `4b4studio/4b4buk`.
4b4buk is a football-first match-discovery and pre-match analysis web app published
under the 4b4apps brand as a separate, isolated product (owner decision 2026-11-14:
own repository, deployment, package and legal assessment; never bundled with
4b4factory or 4b4studio). It runs standalone (own address and icon) and the owner's
private 4b4 Hub may link to it.
Shared studio rules, the AI team and the portfolio live in
[`4b4studio/studio`](https://github.com/4b4studio/studio); this file adds what is
specific to this repository and never overrides the hub's authority rules.

## Read order

1. This file, `docs/STATUS.md`, `docs/DECISIONS.md`.
2. `docs/PRODUCT.md` and `docs/ARCHITECTURE.md` before product or structural changes.
   `docs/RESPONSIBLE_USE.md` before anything touching odds, picks, notifications or
   personalisation. `docs/DATA_SOURCES.md` before adding a data dependency.
3. The assigned issue.

## Language

Speak Polish to the owner. Repository content (code, comments, docs, commits) is
English. Polish UI copy lives in `web/src/i18n.ts`; the backend returns codes only.

## Product rules

- Code computes every statistic (`backend/buk/stats.py`). A language model may only
  select controlled tools (`backend/buk/assistant/tools.py`) and explain their output.
- Every average exposes its sample: count and match list, including excluded matches
  and why. Regulation time, extra time and penalties stay separate. Use only data
  available before the reference kickoff.
- Describing history is not prediction. H2H, streaks, coach changes, corners and cards
  are descriptive until a validated model shows otherwise.
- No odds list, "value" label or confidence badge without a licensed odds source, a
  legal review and a validated, logged probability model (`docs/RESPONSIBLE_USE.md`).
  Never use wording such as "pewniak", "pewny typ" or "gwarantowana wygrana".
- Personalisation may reorder the watch list. It must never learn from betting
  behaviour or steer users towards higher odds or riskier bets.
- Do not scrape competitors or bookmaker sites. Use only sources whose terms allow our
  use, and record the terms checked in `docs/DATA_SOURCES.md`.
- Demo data is fictional and stays labelled as such in the API and the UI.

## Authority, branches and cost

- The owner controls merges into `develop`, promotions to `main`, product direction
  and spending. Follow the hub's work-package flow, owner holds and cross-review rules.
- Work packages start at verified current `develop` on `work/<prefix>-<name>`. The
  proposed prefix `bk` and the name theme "Football stadiums" await owner confirmation
  and registration in the hub's `tools/ai_team/projects.json`.
- No paid API keys, trials, subscriptions, hosting, model calls, notifications to real
  users or publication without explicit owner approval. Refer to secrets by name only
  (for example `SPORTMONKS_API_TOKEN`); never commit, paste or log their values.

## Checks

- Backend: `cd backend && pip install -e ".[dev]" && python -m pytest -q`
  (includes the demo-data freshness check).
- Web: `cd web && npm ci && npm run build` (type check and production build).

## Handoff

End each task with a Polish report: result, branch/PR, checks actually run
(PASS/FAIL/NOT_RUN with command), blockers, and exactly one next action naming who
does it and where.
