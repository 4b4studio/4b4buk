# Architecture

Status: PROPOSED (2026-11-14). The foundation implements the engine, API and PWA on
demo data; storage, ingestion, identity, notifications and the model adapter are
planned packages (see `ROADMAP.md`).

## Context

Approved naming (hub, 2026-11-14): `4b4` is the owner's private Hub/AI factory,
`4b4apps` publishes customer products, `4b4factory` is the customer factory product and
`4b4studio` its first department/MVP. The owner also names 4b4buk as a separately sold
segment. The owner decided on 2026-11-14 that 4b4buk is separate and isolated: own
repository, deployment, package and legal assessment, never bundled with 4b4factory
or 4b4studio (see `DECISIONS.md`). It is a separate deployable with a small
integration contract, not a micro-service of the hub and not a fork. It needs its own
server because of licensed sports data with storage and display rights, user accounts
and the legal isolation of a betting-adjacent product. The hub catalog
(`tools/product/catalog.json`, proposed in hub PR 4b4studio/studio#27) records the
product line.

## Components (one modular monolith)

```
PWA (React, Vite)  --HTTPS-->  API (FastAPI)  -->  PostgreSQL
                                   |  ^
            Web Push  <-- notifier |  | reads            worker (same code, scheduled jobs)
                                   v  |                      |-- ingestion adapters (licensed APIs)
                     stats + interest engine (pure Python)   |-- derived aggregates, data-quality checks
                     assistant tool layer --> LLM adapter    |-- notification triggers
```

- API and worker share one codebase and image; the worker runs scheduled jobs. Add a
  queue only when job volume requires it.
- Provider adapters translate payloads into `domain.py`; provider IDs live in a mapping
  table (`provider, entity, external_id -> internal_id`), never in domain code.
- Planned tables: competitions, seasons, teams, venues, matches (status, kickoff,
  score_90/aet/pens, neutral), team_match_stats (with `includes_extra_time`), lineups
  (status, observed_at), absences (status, source, observed_at), coaches, standings
  snapshots, provider_mappings, raw_payloads (for audit and re-parsing),
  users, preferences, saved_views, feedback, assistant_logs, and later odds_snapshots
  and publications (append-only).
- Every fact keeps `observed_at`, so analyses and backtests can be rebuilt "as of"
  any time without look-ahead.

## When things happen

| Moment | Behaviour |
| --- | --- |
| Before the app opens | Worker refreshes fixtures (daily plus morning), finished results and stats (after full time), absences (several times a day), lineups (polling from ~90 min before kickoff), and precomputes the day's lists. |
| Opening the list | One API call returns ranked lists with reason codes from the precomputed day; the response shows the data timestamp. |
| Opening a match | One bundle call; filter changes re-query the same engine (fast, cacheable), so UI and assistant never disagree. |
| Asking a question | The assistant calls tools (`list_matches`, `match_bundle`, `team_average`, `head_to_head`, `schedule_context`), answers with citations and links to the matching UI view. |
| Lineup or odds update | Worker stores a new observation, recomputes affected flags, and sends a push only for subscribed events, with rate limits. |
| Provider failure or gaps | Serve the last good data with its timestamp and a stale banner; mark missing parts as "no data" (never as zero or "none"); the assistant refuses to answer beyond the data. |

## Identity and Factory integration

- One EU-hosted OpenID Connect provider for the 4b4apps family (shortlist: Zitadel,
  Keycloak; Supabase Auth if Supabase also hosts the database). 4b4buk is a client using
  Authorization Code with PKCE through a backend-for-frontend; the browser holds only a
  host-only, HttpOnly, Secure, SameSite=Lax session cookie.
- The private 4b4 Hub opens 4b4buk by top-level navigation (`factory-module.json`),
  never in a cross-site iframe. Whether customer editions may link a separately
  purchased 4b4buk is an open owner question. Single sign-on comes from the
  provider session.
- Until the shared provider exists, user data is keyed by issuer and subject so the
  account can be joined later without migration of preferences or history.
- Linking policy (which editions may open 4b4buk) lives in the hub catalog
  `tools/product/catalog.json`; this repository owns only the technical contract
  `factory-module.json`, checked by `backend/tests/test_factory_module.py`. The family
  identity provider is a separate tenant, never 4b4buk's own project.
- iOS Home Screen web apps do not share Safari's storage, so users sign in once more
  after installing; onboarding must say so.

## PWA and notifications

PWA first, native later only if push reliability fails the planned experiment. iOS
delivers Web Push only to Home Screen apps (iOS 16.4+), requires a visible notification
for every push and offers no background sync, so every push must carry its full text.
Android allows push without install. Delivery is best-effort; kickoff reminders are
scheduled server-side; lineup alerts depend on the provider's publication time.

## Later sports

Keep the engine sport-neutral at the edges (fixtures, schedule, sample transparency,
lists) and put sport-specific metrics and periods (overtime, innings, shootouts) in
per-sport modules. NBA, NHL and MLB arrive as new adapters and metric sets, not a new app.

## Deployment (when approved)

Smallest viable setup: one small EU virtual machine (or PaaS) running the API/worker
container and PostgreSQL with daily off-site backups, behind TLS. Prices and options
with their verification dates are in the research report; spending needs owner approval.
