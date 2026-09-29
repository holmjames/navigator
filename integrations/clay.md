# Clay

The private and mid-market signal lane, and the enrichment waterfall for every account. Pricing verified against third-party summaries of Clay's 2026-03-11 pricing change (checked 2026-09-28); confirm in-app.

## What Clay is in Navigator

- The scheduler and retry logic for per-row enrichment. Tables run on a schedule or on new rows; columns call providers and HTTP APIs; results push to Snowflake through Clay's Snowflake destination and to n8n through webhooks.
- The place the five plays are built (`plays/`). Tables are built in the UI and exported as JSON to `plays/exports/` for review. Clay's API pushes rows in and receives webhooks out; it does not build tables, so "plays as code" means reviewable, not programmatically recreated (`docs/decisions.md` #16).

## Columns Navigator relies on

| Column type | Used in |
|---|---|
| Find people (Clay people search) | Play 1, committee for private accounts |
| Job change / recently changed jobs | Play 1 |
| Job postings provider | Play 3 |
| News and funding providers | Play 4 |
| Tech detection providers (BuiltWith, Wappalyzer, job-posting tech mentions) | Play 5 |
| Claygent (AI web research) | Plays 2 and 4; the most expensive per row; only on accounts with `fit >= 25` |
| HTTP API | SteadyBase (`integrations/steadybase.md`), MoltSets (`integrations/moltsets.md`), TheSwarm (`integrations/theswarm.md`) |
| Waterfall (email) | MoltSets first, Apollo second; a third provider only if both miss |
| Snowflake destination | Every play table → `raw.clay_rows` with `play`, `source_row_id`, `payload` |
| Webhook | On new row → n8n `clay-signal-webhook` |

## Inputs from Snowflake

A nightly export of `core.account` (non-suppressed, non-holdout, with `fit`) is the source table for the plays, and `core.v_suppressed` domains become each table's exclude filter. Rows are researched once per account per 14 days; a play re-runs only when its source changed.

## Pricing (as reported for the March 2026 change)

| Plan | Monthly | Data credits | Actions |
|---|---|---|---|
| Free | $0 | 100 | 500 |
| Launch | $185 ($167 annual) | 2,500 | 15,000 |
| Growth | $495 ($446 annual) | 6,000 | 40,000 |
| Enterprise | custom | 100,000+ | 200,000+ |

Data credits start at $0.05 each; per-provider costs show in-app only. Actions start under $0.01. At Navigator's volume (about 135,000 credits a month at 500 reps on the demo's defaults) Navan is on Enterprise; the per-credit rate should be at or below the floor.

## Budgets

Per play, in each play file, with an `ops` counter and an alert at 80%.

## To verify

- [ ] Navan's current Clay plan and per-credit rate.
- [ ] Whether the Snowflake destination is enabled on the plan.
- [ ] Credit cost per row for each provider used, in-app.
