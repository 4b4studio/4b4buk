# Product

Status: PROPOSED (2026-11-14). Derived from the owner's brief and the research
report of the same date. Owner approval is required for scope changes.

## Problem and user

The first user is the owner: a Polish football follower who analyses matches before
kickoff and sometimes bets. Today this takes several apps and many taps. Flashscore
spreads one pre-match check across Preview, H2H, Lineups, Odds and Standings tabs.
SofaScore's AI insights and Flashscore's win percentages publish no sample or method.
Bookmaker apps such as Superbet curate "interesting events" as promotions. In the
products we checked, no average opens into the matches behind it.

Jobs to be done:

1. "Show me today's matches worth my evening, and why" — without scrolling all scores.
2. "Give me the pre-match picture of this match in one screen."
3. "Let me check any number: which matches, which period, how many?"
4. "Answer my follow-up questions without me building filters by hand."

## Principles

- Interface first: core comparisons never require typing a prompt.
- Code computes statistics; the assistant selects controlled tools and explains them.
- Every number shows its sample (n and match list); small samples are flagged.
- History is described; prediction is a separate, validated and logged capability.
- Watching, analysing and betting interests are separate lists and separate signals.

## Three lists

| List | Question | v1 signals (each a visible reason) |
| --- | --- | --- |
| Do oglądania (watch) | Will this be good to watch for me? | followed team/competition, top or bottom clash, close in table, recent goal-rich form, knockout stakes, one discovery outside the user's interests |
| Do analizy (analyse) | Is there something unusual to understand? | short rest, rest gap, continental or cup match before/after, extra time or penalties in the previous match, new coach, confirmed key absences, unusual corner or card context |
| Kursy (odds) | Is a price worth a look? | **disabled** until a licensed odds source, legal review and a validated model exist |

Ranking: transparent weighted rules (`backend/buk/interest.py`); ties broken by kickoff.
Warnings (stale H2H, small samples, coach change since last H2H) never add points.

Cold start: before any history the user picks followed teams or competitions in one
step, or skips; the watch list then uses popularity-neutral signals plus discovery.

Feedback ("więcej takich / mniej takich"), planned: stored per reason code and list,
adjusting weights within capped bounds. Feedback on the odds list never changes the
watch or analysis lists, and no list learns to promote higher odds.

## Match page

Mobile order: header (teams, table positions, kickoff, venue, data timestamp) →
"Najważniejsze" (top reasons and warnings) → sticky filters (window 5/10; all vs
home/away context; 90 min vs with extra time; all/league/cups) → side-by-side
comparison (form strip, points per game, goals for/against, corners for/against,
cards, shots, shots on target, each with n and the league average) → head-to-head →
schedule and rest → lineups, absences and rotation risk → data quality.
Desktop: two columns (comparison and H2H left; schedule, absences, quality right).

- Tapping any value opens the sample sheet: date, opponent, venue, competition,
  90-minute score with extra-time/penalty markers, value, and excluded matches with
  their reason (missing statistic, statistics covering extra time).
- Filters live in the URL, so a link or reload restores the exact comparison.
- Head-to-head shows the last meeting first (date, venue, days ago, result), a 90-minute
  balance, coach changes since the last meeting, form before the last meeting vs now
  (with n), and a staleness warning beyond two years. It is labelled description, not
  prediction (see the evidence summary in `RESPONSIBLE_USE.md`).
- Lineups: not available / predicted / confirmed with timestamps. Absences: confirmed
  or doubtful, with source and time; "no data" is never shown as "no absences".
  Rotation risk is a schedule heuristic and says so.

## Personalisation

| Option | v1 | Reason |
| --- | --- | --- |
| Followed teams/competitions | Yes | Drives the watch list; cheap and explicit |
| Remembered filters | Yes (URL + per-user default) | Removes repeated taps |
| Pinned statistics | Next | Needs accounts; simple ordering data |
| View profiles (Gole, Rożne, Forma) | Next | Presets over pins; test after usage data exists |
| Learned preferences | Later, bounded | Only from explicit feedback and dwell on analysis, never from betting |

## Assistant

The interface answers routine questions; the assistant handles follow-ups such as
"Pokaż średnie rożnych z ostatnich 10, osobno dom i wyjazd", "Kiedy grali ostatnio?",
"Które zespoły są przed albo po pucharach?", "Co przemawia przeciw tej ocenie?".
Each answer cites tool outputs (sample IDs, data timestamp) and links into the UI
view that shows the same numbers. Without a configured model the app stays fully
usable. Model choice and spend are owner decisions.

## Odds (later)

Show four separate axes: price (with implied probability and margin); probability
estimate (market de-margined, later a validated model, with an interval); data
completeness; expected value after Polish tax. Publish nothing as a pick unless it is
written to the append-only publication log first (see `RESPONSIBLE_USE.md`).

## Scope

MVP: watch and analysis lists, match page with sample transparency, one licensed
football data source, accounts with followed teams and remembered filters, PWA install.
Next: pinned statistics and profiles, assistant over tools, lineup and kickoff push
notifications, feedback. Later: odds axes after legal review, probability model with
public track record, NBA/NHL/MLB.
Not now: native apps, live in-play features, social or copy-betting, affiliate links,
paid tiers, scraping, player-level props.
