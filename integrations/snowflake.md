# Snowflake

Memory and scoring. `RAW`, `CORE`, `MARTS` (`data/schema.sql`), dbt on Snowflake tasks, and Cortex for model calls inside SQL where the region allows.

## Roles and warehouses

| Role | Grants |
|---|---|
| `NAVIGATOR_LOADER` | insert on `RAW`; used by the connectors, Clay's destination, n8n |
| `NAVIGATOR_TRANSFORM` | dbt: read `RAW`, write `CORE` and `MARTS` |
| `NAVIGATOR_APP` | read `MARTS`, read `CORE.drafts/decisions/contact`, write `CORE.touches/drafts/decisions/audit/switches`; used by the Slack app and the agents runner |
| `NAVIGATOR_DEV` | everything above on the dev database |
| `GTM_SIGNALS_RO_<TENANT>` | SteadyBase's read-only role on its shared views, if shared |

One X-Small warehouse `NAVIGATOR_WH` with auto-suspend at 60 seconds for the hourly build, scoring, and app reads. Budget: about 90 credits a month at 500 reps (`ops/prices.yml`).

## Tasks

| Task | Schedule | Does |
|---|---|---|
| `hourly_build` | every hour at :05 | `dbt run --select core marts` (incremental) |
| `nightly_score` | 00:45 per timezone bucket | `data/scoring.sql`, then the reason-code job |
| `nightly_batch` | after `nightly_score` | the agents' batch (Cortex path), or signals n8n to file the OpenAI batch |
| `signal_rescore` | on new rows in `raw.steadybase_signals` or `raw.clay_rows` (stream) | scoring for affected accounts only |

## Cortex

Snowflake Cortex AI hosts OpenAI models on Azure-region accounts (announced 2025). If Navan's account is on Azure, briefs, drafts, QA, and reason codes run as `SNOWFLAKE.CORTEX.COMPLETE('<model>', <prompt>)` inside the nightly task, batched by SQL. If the account is on AWS, the same jobs run through the OpenAI Batch API filed from n8n (`ingest/n8n/openai-batch.json`). `docs/decisions.md` open item C.

## Cost controls

Resource monitor on `NAVIGATOR_WH` at 150 credits a month with notify at 80% and suspend at 110%. Incremental models only; no full refresh outside a migration.

## To verify

- [ ] Navan's cloud and region (Cortex model availability).
- [ ] Edition (Standard vs Enterprise) for the credit rate.
- [ ] Whether the Salesforce connector is the native one or Fivetran.
- [ ] Whether SteadyBase's tenant views are already shared into the account.
