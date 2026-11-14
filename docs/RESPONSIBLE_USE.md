# Responsible use: odds, picks and personalisation

Status: PROPOSED rules (2026-11-14). Legal points are UNVERIFIED and need a Polish
lawyer before any odds, links or picks reach users. This is not legal or tax advice.

## Rules for the product

1. No odds list, value label, EV figure or confidence badge until all of: a licensed
   odds source with display rights, a written legal review, a validated probability
   model, and the publication log below.
2. Polish users only ever see operators on the Ministry of Finance's current list of
   licensed operators (store the list's snapshot date). No unlicensed brands, no links
   to them. Whether unlicensed prices may be used internally and unbranded is a lawyer
   question.
3. No affiliate links in v1. Any future odds card with a link is treated as advertising
   with the required warnings and an 18+ gate.
4. Odds are hidden by default and free to hide permanently. An 18+ confirmation guards
   the odds module.
5. Personalisation never uses betting behaviour, never rewards higher odds, and never
   escalates stakes or frequency. Watch and analysis lists ignore odds entirely.
6. Banned wording: "pewniak", "pewny typ", "100%", "gwarantowana wygrana", "bez
   ryzyka", "odrób straty", "zarabiaj/inwestuj", urgency prompts. Use "szacowane
   prawdopodobieństwo", "kurs wyższy niż szacunek" and show the full track record,
   including losses and sample size.

## Four separate axes (when odds return)

| Axis | Meaning | Shown as |
| --- | --- | --- |
| Price | bookmaker odds and implied probability including margin | odds, margin % |
| Probability | de-margined market estimate; later a validated model with an interval | % with interval and method |
| Data quality | completeness and freshness of lineups, absences, sample sizes | grade with reasons |
| Expected value | after Polish tax and margin, only with a validated model | % with interval; hidden otherwise |

A high price is not high confidence: confidence describes the estimate, never the
chance of winning.

## Polish tax (to verify against current law)

Operators commonly deduct a 12% gaming tax from the stake, and single wins above
2,280 PLN are taxed at 10%. At odds 2.00 with the stake tax, the effective odds are
1.76 and the break-even probability rises from 50.0% to about 56.8%. EV shown to users
must include the tax unless a verified tax-free offer applies.

## Publication log (append-only)

Before a pick or highlighted price is shown, write a record: UTC timestamp, operator,
market and line, odds, tax mode, de-margined market probability, model probability and
version, data-quality grade, rationale (reason codes), and a hash of the record. Never
edit; corrections are new versions. After the match add closing odds, result,
closing-line comparison and proper scores (log loss, RPS, Brier). Track records include
every published item.

Evaluation needs patience: at odds near 2.00 a genuine 2% edge needs on the order of
10,000 independent bets to stand two standard errors above zero, so short winning runs
prove nothing.

## Evidence summary (what the app may claim)

- Describe only: raw last-5/10 form tables, H2H, rest days, extra time in the previous
  match, corners and cards averages, coach tenure.
- Model features after validation: strength ratings based on goal margins with recency
  weighting, league-level home advantage, xG where licensed.
- Warn: small samples, stale H2H, new coach ("new manager bounce" is largely regression
  to the mean in published studies).
