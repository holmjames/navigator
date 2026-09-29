# data/ — schema, dbt, scoring

**Owns:** `RAW`, `CORE`, `MARTS` in Snowflake; the dbt project; `scoring.sql`; the resolver's private-book ladder; the suppression view; the playbook and manager marts.

**Reads:** everything `ingest/` lands in `RAW`.
**Writes:** `CORE.*`, `MARTS.*`.
**Called by:** Snowflake tasks (hourly dbt build, nightly scoring), the reason-code job, `agents/`, `slack/`.

## Interface

| Name | Kind | Contract |
|---|---|---|
| `core.account`, `core.contact`, `core.signals`, ... | tables | `schema.sql` is the DDL. Columns are added, never renamed. |
| `core.v_suppressed` | view | `(account_id, contact_id, why)`. `contact_id` null means the whole account. |
| `marts.playbook_daily` | view | One row per account on today's board. This is the only thing the Slack app reads. |
| `marts.manager_daily`, `marts.actioned_24h`, `marts.cost_per_meeting` | views | The manager view. |
| `core.v_score_inputs` | view | The scoring components. `scoring.sql` materializes into `core.scores`. |
| `resolve_private(name, domain, linkedin_company, sfdc_id)` | UDF | The private-book ladder. Returns `(account_id, method, confidence, status)`. Status `ambiguous`, `conflict`, or `no_match` writes to `core.review_queue` and returns null `account_id`. |

## The private-book ladder

Same shape as SteadyBase's (see `integrations/steadybase.md`), fewer rungs:

| Rung | Confidence |
|---|---|
| `sfdc_id` already mapped in `core.account_ids` | 1.00 |
| `domain` (registrable, normalized, not a free-mail or shared domain from `core.shared_domains`) | 0.92 |
| `linkedin_company` slug | 0.92 |
| legal name plus agreeing country | 0.85 |
| legal name alone | 0.60, flagged weak, never a match on its own |

Rules: each rung votes; two candidates at any rung is `ambiguous`; two rungs disagreeing is `conflict`; a weak-only match is `no_match` with candidates. A domain claimed by more than one account is `domain_collision` and goes to the queue with both. Nothing is guessed.

## dbt layout

```
data/dbt/
├── dbt_project.yml
├── models/
│   ├── raw/          sources.yml only
│   ├── core/         account.sql, contact.sql, signals.sql, briefs.sql (incremental), warm_paths.sql, ...
│   ├── marts/        playbook_daily.sql, manager_daily.sql, actioned_24h.sql, cost_per_meeting.sql
│   └── schema.yml    tests: not_null, unique, accepted_values, and the custom ones below
└── tests/
    ├── signals_https.sql          fails on any core.signals row without https://
    ├── account_ids_unique.sql     fails on any (id_type,id_value) with two account_ids
    └── briefs_fresh.sql           fails if playbook_daily shows a brief past fresh_until
```

Core models are incremental on `_loaded_at`. Scoring runs as a Snowflake task after the hourly build and again for accounts with new signals (`raw.steadybase_signals` or `raw.clay_rows` rows in the last hour).

## Acceptance

- [ ] `schema.sql` applies cleanly to an empty database twice (idempotent).
- [ ] `evals/fixtures/book.csv` (200 fictional accounts, 15 public) loads; `core.account` has 200 rows; `core.review_queue` has the 6 planted ambiguities.
- [ ] `scoring.sql` on the fixture gives Larkspur Dynamics `score = 91, priority = 'P1'` with components 37/32/12/10.
- [ ] dbt tests pass; `signals_https` fails when a row with an `http://` URL is inserted into `raw.steadybase_signals`, and the row lands in `raw.ingest_rejects`.
- [ ] `marts.playbook_daily` returns no holdout accounts and no suppressed accounts.
- [ ] Every table has `_loaded_at`.

## Not in scope

Anything that calls a model or a vendor. That is `ingest/` and `agents/`.
