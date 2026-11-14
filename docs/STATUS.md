# Status

Updated 2026-11-14.

## Current state: foundation on demo data

| Area | State |
| --- | --- |
| Statistics engine | Implemented: windows, home/away, 90 min vs extra time, exclusions with reasons, league reference, form, H2H, schedule context, rotation heuristic, standings |
| Watch and analysis lists | Implemented as transparent rules with reason codes; one discovery slot |
| Odds list | Disabled by design (`NO_ODDS_SOURCE`) |
| Match bundle API | Implemented (`/api/v1/matches`, `/api/v1/matches/{id}`, `/api/v1/teams/{id}/average`) |
| Assistant | Tool specifications and dispatcher only; no model calls |
| PWA | Today screen, match screen, sample sheet, URL filters, manifest, placeholder icons, shell-only service worker |
| Data | Fictional demo dataset from a deterministic generator; no real provider |
| Storage, accounts, notifications, deployment | Not started |

## Checks (2026-11-14, local)

- `cd backend && python -m pytest -q` — PASS (33 tests, includes demo freshness).
- `cd web && npm run build` — PASS (TypeScript 7.0, Vite 8.3).
- Manual: Playwright screenshots on 390×844 and 1366×900, no console errors,
  service worker registered, path traversal returns the app shell — PASS.
- Cross-provider review — NOT_RUN.

## Known issues

- Starlette warns that `httpx` in the test client is deprecated in favour of `httpx2`;
  verify that package's provenance before switching.
- Icons are placeholders until the owner approves a mark.
- Head-to-head detail rows lack per-match statistics until storage exists.
- Demo history before 2026/27 covers only head-to-head meetings, so "form before the
  last H2H" uses small samples (shown with n).

## Next

See `ROADMAP.md`. The next package needs owner decisions on the data-provider trial
and the work-branch prefix.
