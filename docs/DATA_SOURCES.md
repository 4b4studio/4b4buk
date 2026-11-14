# Data sources

Status: PROPOSED. Checked 2026-11-14 through web-search results only (direct page
access was blocked in the research environment). Treat every price and term as
"to verify" before any purchase; purchases and trials need owner approval.

## Candidates

| Source | Role | Verified points | To verify |
| --- | --- | --- | --- |
| Sportmonks Football API v3 | Primary candidate | Ekstraklasa, 1. Liga and Polish Cup coverage; plans from €29/€99/€249 per month; storage and display in own product allowed by its own pages; scores split into current/extra time/penalty shoot-out; add-ons for xG, expected lineups (human-curated), predictions, odds | Conflicting "personal and non-commercial" wording in the terms; history depth beyond 3 seasons; sidelined/coach/H2H endpoints; per-period statistics |
| API-Football (api-sports) | Prototype and cross-check | Free 100 requests/day; paid from $19/month; 1,200+ competitions; injuries since 2021; coach careers; H2H endpoint | Terms grant no licence to publish; storage and display rights in writing; whether stats include extra time |
| football-data.org | Fallback for top competitions | Clear regulation/extra-time/penalty fields | Polish coverage tier and commercial price; data must be deleted on cancellation |
| Sportradar, Stats Perform (Opta), STATSCORE | Official/enterprise options | Quote-based; STATSCORE is Polish with official partnerships; Sportradar offers an ID-mapping service | Price, licence for betting-adjacent use |
| football-data.co.uk | Research only | Free historical results, statistics and closing odds, including Poland | Not for commercial use |
| The Odds API | Odds reference (non-Polish books) | History since 2020, 5-minute snapshots since 2022, plans from $30/month | No Polish-licensed bookmakers; display terms |
| Odds-API.io | Polish bookmaker odds candidate | Lists STS, Superbet, Betclic and Fortuna PL; aggregates publicly displayed odds | Data provenance and written display/storage rights; legal review |

Excluded: scraping SofaScore, Flashscore, OddsPortal, FBref, Understat, Transfermarkt or
bookmaker sites; their terms bar it or the data comes from licensed third parties.

## Feature → data matrix

| Feature | Data | Source (planned) | Limits | When missing |
| --- | --- | --- | --- | --- |
| Lists of the day | fixtures, standings, recent results | primary | coverage per plan | list shows only covered competitions, says so |
| Form and averages | per-match team stats | primary | stats may start in recent seasons; ET handling varies | match listed as excluded with reason; n shown |
| Head-to-head | historical fixtures | primary (+ history add-on) | depth per competition | "only N meetings since <season>" |
| Schedule context | fixtures in all competitions | primary | lower-tier cups may be absent | "next fixture unknown" rather than wrong rest days |
| Lineups | lineups with publication time | primary | confirmed ~shortly before kickoff | status "not available"; no inference |
| Absences | sidelined/injuries | primary or complement | update frequency hours | "no data" ≠ "none" |
| Coach changes | coach history | primary or complement | patchy outside top leagues | not shown, no warning claimed |
| Odds axes | timestamped odds by licensed operator | to be decided after legal review | Polish books rarely available | odds list disabled |

## Experiment before committing

Pull the same 30 fixtures (10 Ekstraklasa, 10 Polish Cup including extra time and
penalties, 10 UEFA) from two providers. Success: corners, cards, shots, shots on
target and fouls present in ≥ 90% of fixtures; separable 90/ET/penalty scores; lineups
≥ 30 minutes before kickoff; stable IDs after one week.
