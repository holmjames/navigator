# Scoring

The score is a formula in SQL (`data/scoring.sql`). The model writes the reasons a rep reads; it never touches the numbers. Weights are `weights_version = 'v1'` until there are enough outcomes to refit (see `docs/pilot.md`).

```
score = fit (0–40) + signal (0–35) + timing (0–15) + relationship (0–10)
```

| Priority | Score |
|---|---|
| P1, act now | 80 and above |
| P2 | 65 to 79 |
| P3 | 50 to 64 |
| P4, monitor | below 50 |

Priority decides whether an account is on today's board and how it sorts. Tier (A, B, C) is a separate thing: it decides how much autonomy the agents get and comes from segment and country, not from the score. See `docs/tiers.md`.

## Fit (0 to 40)

Deterministic from firmographics. Four components.

**Employees (0 to 10)** from `account.employees`:

| Band | Points |
|---|---|
| under 50 | 1 |
| 50 to 199 | 6 |
| 200 to 999 | 8 |
| 1,000 to 4,999 | 10 |
| 5,000 to 19,999 | 9 |
| 20,000 and up | 6 |
| unknown | 3 |

**Travel intensity (0 to 14)**, three parts added:

| Part | Rule | Points |
|---|---|---|
| Countries with offices | 1 / 2 to 3 / 4 or more | 0 / 3 / 6 |
| Office count | 1 / 2 to 4 / 5 or more | 0 / 2 / 4 |
| Industry travel index | lookup in `core.industry_travel_index` (0 to 4): consulting, professional services, software with a field sales motion, logistics, construction, healthcare services, industrial with field service score 2 to 4; local retail, restaurants, and pure remote software score 0 to 1 | 0 to 4 |

**Stack (0 to 10)** from tech detection:

| Detected | Points |
|---|---|
| A displacement target: Concur, Spendwell, TravelPerk, Egencia, Emburse, Zoho Expense, Kestrel Travel, or another managed-travel platform | 10 |
| A corporate card program only (Amex, Harbor Card, Kestrel card, Divvy) | 5 |
| Nothing detected | 3 |
| Meridian Travel (customer) | excluded by suppression before scoring |

**Growth (0 to 6)** from 24-month headcount change:

| Change | Points |
|---|---|
| 30% or more | 6 |
| 15% to 29% | 4 |
| 0% to 14% | 2 |
| negative | 0 |

## Signal (0 to 35)

The strongest signal in the last 90 days, adjusted for evidence and age, plus a fifth of the second strongest, capped at 35.

**Base points by `signal_type`:**

| signal_type | Base | Typical source |
|---|---|---|
| `vendor_change` (T&E or travel tool consolidation, vendor switch, RFP) | 30 | earnings call, filing, press release |
| `cost_program` naming travel or T&E | 26 | earnings call, deck |
| `leadership_change` (new CFO, controller, VP finance, head of procurement) | 22 | 8-K, LinkedIn job change |
| `travel_role_hiring` (travel manager, T&E lead, global mobility) | 20 | job posting |
| `expansion` (new office, new country, headcount plan) | 18 | call, press release, job postings by location |
| `funding` (round announced) | 16 | press release, filings |
| `m_and_a` (announced or pending) | 16 | 8-K, 425, S-4 |
| `finance_hiring` (three or more open finance or AP roles) | 14 | job postings |
| `headcount_growth` (signal-level, not the fit term) | 10 | headcount data |
| `other` | 6 | anything else receipted |

**Evidence multiplier** from `evidence_tier`:

| Tier | Meaning | Multiplier | Quotable in outreach |
|---|---|---|---|
| 1 | Verbatim quote from a call, filing, deck, or IR page, with a receipt | 1.00 | Yes, verbatim |
| 2 | An artifact with a URL: job posting, press release, funding announcement, public post | 0.85 | Yes, cited as the artifact |
| 3 | Inferred (a research summary without a quotable source) | 0.60 | No |

**Recency multiplier** from days since `event_date`:

| Age | Multiplier |
|---|---|
| 0 to 14 days | 1.00 |
| 15 to 45 days | 0.80 |
| 46 to 90 days | 0.50 |
| over 90 days | 0 |

```
adjusted(s) = base(signal_type) * evidence(tier) * recency(age)
signal      = min(35, max(adjusted) + 0.2 * second_max(adjusted))
```

## Timing (0 to 15)

Three parts added, capped at 15.

**Earnings calendar (public companies only; private accounts get a flat 3):**

| Position | Points | Note |
|---|---|---|
| 1 to 28 days after the last call | 6 | The close is done and the call's content is fresh |
| 29 to 56 days after | 3 | |
| Within 14 days before the next call | 0 | Quiet period; `decide()` also defers finance-persona touches here |
| Otherwise | 2 | |

**New-in-role buyer** (best persona on the committee, by `role_start`):

| Days in role | Points |
|---|---|
| under 30 | 2 (too new to buy) |
| 30 to 120 | 6 |
| 121 to 180 | 3 |
| over 180 or unknown | 0 |

**Fiscal year end** 60 to 120 days out (budget planning), when known: 3.

## Relationship (0 to 10)

From `core.warm_paths` (TheSwarm) and CRM history, capped at 10.

| Fact | Points |
|---|---|
| Strongest warm path strength 0.70 or higher | 10 |
| 0.50 to 0.69 | 6 |
| 0.30 to 0.49 | 3 |
| No path | 0 |
| Closed-lost opp in the last 18 months with reason `timing` or `budget` | +4 |
| Former customer | +4 |

At launch most accounts will score 0 here because warm paths depend on employee opt-in to TheSwarm. That is expected; the term grows into its weight.

## Worked example: Larkspur Dynamics (fictional)

Inputs: 5,200 employees; offices in 6 countries, 14 offices; industrial with field service (index 2); Concur detected; headcount up 31% over 24 months. Signals: on the Q3 call yesterday the CFO said "We're consolidating our travel and expense tools onto a single platform in the first half" (tier 1, `vendor_change`); nine open finance roles from job postings (tier 2, `finance_hiring`, 12 days old). Public; last earnings call 1 day ago. Controller 58 days in role. Warm path: an AE worked with the controller 2019 to 2021, strength 0.82.

| Term | Arithmetic | Points |
|---|---|---|
| Fit: employees | 5,000 to 19,999 | 9 |
| Fit: travel | 6 countries (6) + 14 offices (4) + index (2) | 12 |
| Fit: stack | Concur | 10 |
| Fit: growth | 31% | 6 |
| **Fit** | | **37** |
| Signal: strongest | 30 × 1.00 × 1.00 | 30.0 |
| Signal: second | 14 × 0.85 × 1.00 = 11.9, × 0.2 | 2.4 |
| **Signal** | min(35, 32.4) | **32** |
| Timing: calendar | 1 day after the call | 6 |
| Timing: new in role | 58 days | 6 |
| Timing: fiscal year end | unknown | 0 |
| **Timing** | | **12** |
| **Relationship** | 0.82 | **10** |
| **Score** | 37 + 32 + 12 + 10 | **91, P1** |

Tier: 5,200 employees is enterprise by employee count, but Larkspur is a mid-market territory account in the fixture (segment is a Salesforce field, not a derived one), so tier B: drafts wait for the rep. See `docs/tiers.md`.

## Reason codes

GPT-5 nano writes three lines from the component table above, using `agents/prompts/reasons.md`. The prompt receives the components and the signals' quotes, never the raw account row. Reasons must name the component they come from and must not introduce facts absent from the inputs.

## Refit

`weights_version` is stored on every `core.scores` row. A refit is a new version, never an edit. The first refit happens when `core.outcomes` holds at least 300 meetings attributable to Navigator touches (roughly month two at 500 reps), and it is a logistic fit of meeting-booked on the four terms, reviewed by a person, with the previous version kept for comparison. The pilot pod cannot refit; it proves the plumbing.
