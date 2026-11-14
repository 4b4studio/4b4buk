# Roadmap

PROPOSED (2026-11-14). Package names follow the proposed "Football stadiums" theme and
change if the owner picks another. Team per package: one implementing agent, one
other-provider reviewer, the owner for decisions and phone checks. Durations are
agent working estimates, excluding waits for owner decisions, purchases or reviews.

| # | Package | Scope | Acceptance | Depends on | Estimate |
| --- | --- | --- | --- | --- | --- |
| 0 | `work/bk-anfield` Foundation | This repository's current content | Tests and build pass; demo labelled; owner can open both screens | — | done locally |
| 1 | `work/bk-bernabeu` Data trial and storage | PostgreSQL schema and migrations, provider mapping, observed-at timestamps, one adapter, ingestion for 3 competitions, 30-fixture comparison | Engine runs on real data for Ekstraklasa, Puchar Polski and one UEFA competition; experiment thresholds reported; no secrets in Git | Owner approves a trial and cost | 3–5 days |
| 2 | `work/bk-camp-nou` Accounts and preferences | Identity provider decision, backend-for-frontend session, followed teams/competitions, remembered filters, data keyed by issuer and subject | Sign-in works in desktop browser and installed iOS/Android PWA; preferences follow the user across devices | Owner picks the identity option | 3–4 days |
| 3 | `work/bk-de-kuip` Lists v1 on real data | Threshold calibration, cold start, feedback "więcej/mniej takich" with capped weights, discovery tuning | Two weeks of owner use; top-3 of each list rated useful on most days in a simple log | 1, 2 | 3–4 days + 2 weeks use |
| 4 | `work/bk-estadio-da-luz` Match page v2 | Pinned statistics, view profiles, H2H match statistics, opponent strength context, accessibility pass | Owner answers the six core questions in ≤ 60 s on the phone, timed against the current app | 1, 2 | 4–6 days |
| 5 | `work/bk-fratton-park` Notifications | Web Push for lineups, kickoff and schedule changes; delivery measurement | ≥ 95% shown within 60 s on 5 iOS and 5 Android devices, no unexplained revocations | 2, deployment | 3 days + 2 weeks test |
| 6 | `work/bk-goodison` Assistant | Model adapter over existing tools, citations to UI views, cost caps, 30-question evaluation set | Every answer cites tool output; no numbers outside tools; cost per question within the approved cap | 1, owner approves model spend | 4–6 days |
| 7 | `work/bk-highbury` Deployment and operations | EU hosting, backups with a restore drill, monitoring, data-freshness and cost alerts | Restore drill passes; alerts fire in a test; monthly cost report | Owner approves hosting | 2–3 days |
| 8 | `work/bk-ibrox` Odds research track | Legal review, licensed source, de-margined market probabilities in shadow mode, publication log | Written legal sign-off; shadow log runs for 4 weeks without showing users | Lawyer, licensed source | calendar-bound |

Later: validated probability model with a public track record; NBA, NHL and MLB adapters.
Not now: native apps, in-play features, social or copy-betting, affiliate links, paid tiers.
