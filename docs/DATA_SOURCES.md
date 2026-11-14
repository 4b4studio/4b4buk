# Data sources

Status: PROPOSED. Checked 2026-11-14 through web-search results, with a second
adversarial pass the same day (direct page access was blocked in the research
environment). Treat every price and term as
"to verify" before any purchase; purchases and trials need owner approval.

## Candidates

| Source | Role | Verified points | To verify |
| --- | --- | --- | --- |
| Sportmonks Football API v3 | Primary candidate | Ekstraklasa, 1. Liga and Polish Cup coverage; plans from €29/€99/€249 per month net (€24/€79/€199 billed yearly); terms allow monetising a product built on the data and forbid reselling raw data; Premium Odds and Expected Lineups need Growth or higher; scores split into current/extra time/penalty shoot-out; add-ons for xG, expected lineups (human-curated), predictions, odds | "Personal and non-commercial" wording appears to cover website materials (confirm in writing); history depth beyond 3 seasons; sidelined/coach/H2H endpoints; per-period statistics |
| API-Football (api-sports) | Prototype and cross-check | Free 100 requests/day; paid from $19/month; 1,200+ competitions; injuries since 2021; coach careers; H2H endpoint | Terms grant no licence to publish; storage and display rights in writing; whether stats include extra time |
| football-data.org | Fallback for top competitions | Clear regulation/extra-time/penalty fields | Polish coverage tier and commercial price; data must be deleted on cancellation |
| Sportradar, Stats Perform (Opta), STATSCORE | Official/enterprise options | Quote-based; STATSCORE is Polish with official partnerships; Sportradar offers an ID-mapping service | Price, licence for betting-adjacent use |
| football-data.co.uk | Research only | Free historical results, statistics and closing odds, including Poland | Not for commercial use |
| The Odds API | Odds reference (non-Polish books) | History since 2020-06-06 on paid plans, 5-minute snapshots since 2022-09, plans from $30/month | No Polish-licensed bookmakers; its EU region includes Pinnacle and Betfair, unlicensed in Poland: internal benchmark only, after legal review |
| Odds-API.io | Polish bookmaker odds candidate | Lists STS, Superbet, Betclic and Fortuna PL; data from partnerships and public sources; redistribution only with written consent | Data provenance and written display/storage rights; legal review |

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
