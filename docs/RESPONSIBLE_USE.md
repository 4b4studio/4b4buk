# Responsible use: odds, picks and personalisation

Status: PROPOSED rules (2026-11-14). Legal and tax points were checked against primary
sources on 2026-11-14 (search-based, second adversarial pass); a Polish lawyer must
still review before any odds, links or picks reach users. This is not legal or tax advice.

## Rules for the product

1. No odds list, value label, EV figure or confidence badge until all of: a licensed
   odds source with display rights, a written legal review, a validated probability
   model, and the publication log below.
2. Polish users only ever see operators on the Ministry of Finance's current list of
   licensed operators ("Legalny hazard"), matched by exact .pl domain; store the list's
   snapshot date. No unlicensed brands, no links to them: naming or linking them risks
   liability under art. 110a of the Fiscal Penal Code (a court imposed a PLN 150,000
   fine in case II K 1132/22). Whether unlicensed prices may be used internally and unbranded is a lawyer
   question.
3. No affiliate links in v1. Any future odds card with a link is treated as advertising
   with the required warnings and an 18+ gate. Art. 29b of the Gambling Act allows
   advertising of licensed betting under conditions but does not expressly allow
   promotion (bonuses, free bets); a legal opinion is required first.
4. Odds are hidden by default and free to hide permanently. An 18+ confirmation guards
   the odds module.
5. Personalisation never uses betting behaviour, never rewards higher odds, and never
   escalates stakes or frequency. Watch and analysis lists ignore odds entirely.
6. Banned wording: "pewniak", "pewny typ", "100%", "gwarantowana wygrana", "bez
   ryzyka", "odrób straty", "zarabiaj/inwestuj", urgency prompts. Use "szacowane
   prawdopodobieństwo", "kurs wyższy niż szacunek" and show the full track record,
   including losses and sample size.
   Legal basis: art. 29b (no linking betting with easy wins) and art. 7(16) of the Act
   on counteracting unfair market practices (no claims that a product raises the chance
   of winning).

## Four separate axes (when odds return)

| Axis | Meaning | Shown as |
| --- | --- | --- |
| Price | bookmaker odds and implied probability including margin | odds, margin % |
| Probability | de-margined market estimate; later a validated model with an interval | % with interval and method |
| Data quality | completeness and freshness of lineups, absences, sample sizes | grade with reasons |
| Expected value | after Polish tax and margin, only with a validated model | % with interval; hidden otherwise |

A high price is not high confidence: confidence describes the estimate, never the
chance of winning.

## Polish tax (checked 2026-11-14)

The gaming tax is 12% of stakes (Gambling Act art. 73-74), paid by the operator; the
2024 draft raising it to 16% was not enacted. Operators usually deduct it from the
stake, but the deduction is their commercial term: 12%, 6% or 0% (for example Betclic
since 2026-05-19, per secondary sources). Store the deduction per operator and date;
effective odds are (1 - deduction) x odds. At odds 2.00 the break-even probability is
56.8% with 12% and 53.2% with 6%.

A single win above 2,280 PLN is taxed at 10% PIT on the whole payout, withheld by the
operator. At odds 2.00 this applies to stakes above about 1,295 PLN and lowers
effective odds to 0.792 x odds (break-even 63.1%). A rise to 15% was vetoed on
2025-12-18. EV shown to users must include both steps.

## Publication log (append-only)

Before a pick or highlighted price is shown, write a record: UTC timestamp, operator,
market and line, odds, tax mode, de-margined market probability, model probability and
version, data-quality grade, rationale (reason codes), and a hash of the record. Never
edit; corrections are new versions. After the match add closing odds, result,
closing-line comparison and proper scores (log loss, RPS, Brier). Track records include
every published item.

Evaluation needs patience: at odds near 2.00 a genuine 2% edge (return per unit staked)
reaches two standard errors only after about 10,000 independent bets, and even then only
about half the time; 80% power needs about 20,000. Short winning runs prove nothing.

## Evidence summary (what the app may claim)

- Describe only: raw last-5/10 form tables, H2H, rest days, extra time in the previous
  match, corners and cards averages, coach tenure.
- Model features after validation: strength ratings based on goal margins with recency
  weighting, league-level home advantage, xG where licensed.
- Warn: small samples, stale H2H, new coach ("new manager bounce" is largely regression
  to the mean in published studies).
