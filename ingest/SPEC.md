# ingest/ — how each source lands in Snowflake

**Owns:** one landing path per source, the resolver call on every account or contact row, the reject counter, the n8n workflow exports, the cursor store.

**Writes:** `raw.*`, `core.review_queue`, `raw.ingest_rejects`, `core.cost_events`.
**Reads:** vendor APIs and webhooks, `core.account_ids` (for the resolver), `core.v_suppressed` (to build exclude lists).

Code is minimal here by design (see `docs/decisions.md` #4): every source either pushes, shares, or is polled with one HTTP call on a cursor.

| Source | Path | Cadence | Dedupe key | Notes |
|---|---|---|---|---|
| **SteadyBase signals** | Tenant views shared into Snowflake (`GTM_SIGNALS.TERRITORY.V_TENANT_*`) read by dbt; plus the delta feed `whats_new(since=<cursor>)` and `bulk_since(cursor=<cursor>)` polled hourly by one n8n flow that inserts into `raw.steadybase_signals` | Hourly | `event_key` | Cursor stored in `core.cursors`. `truncated=true` means poll again at once. Retention on the feed is 30 days; a cursor older than that backfills with `bulk_company`. |
| **SteadyBase people** | `pg_people(new_in_role_days=120)` per persona, nightly, into `raw.steadybase_people`; identity only | Nightly | `(account_id_sb, linkedin_url)` | Never returns email or phone. |
| **SteadyBase calendar** | `pg_future_events(days=45)` nightly into `raw.steadybase_events` | Nightly | `(ticker, report_date)` | Feeds `next_earnings_call_date`. |
| **Clay** | Clay's Snowflake destination writes each play table to `raw.clay_rows` (one table, `play` column); a Clay webhook per play hits n8n on new rows to trigger scoring for that account | On row change | `(play, source_row_id)` | Exclude list pulled from `core.v_suppressed` into each table's filter nightly. |
| **Salesforce** | Snowflake's native Salesforce connector (or Fivetran) to `raw.sfdc_*` | Nightly, 00:30 | SFDC id | Fields listed in `integrations/salesforce.md`, including the three custom ones. |
| **Apollo events** | Apollo webhook → n8n → `raw.apollo_events`; replies also trigger the reply flow | Live | `event_id` | |
| **Nooks** | Webhook if available, else nightly export to `raw.nooks_calls` | Live or nightly | `call_id` | See `integrations/nooks.md`; unverified. |
| **TheSwarm** | API, weekly per worked account (accounts with a decision in the last 30 days), into `raw.swarm_paths`; also as a Clay column inside the plays | Weekly | `(target_linkedin, connector_email)` | Credits: 1 per person export. |
| **MoltSets** | Called from Clay columns in the waterfall, results land through Clay; also callable from n8n for the reply flow's referral contacts | On demand | `linkedin_url` | Always with `exclude_company_domain`. |

## The resolver on every row

Every account-shaped row (`raw.clay_rows`, `raw.sfdc_account`, `raw.steadybase_*`) passes through the resolver before it can reach `CORE`:

- Public: SteadyBase `find_companies(resolve={...})` with whatever identifiers the row has; or the `external_id` route with the Salesforce id. `resolved` writes `core.account_ids`; anything else writes `core.review_queue`.
- Private: `resolve_private(name, domain, linkedin_company, sfdc_id)` in Snowflake (`data/SPEC.md`).
- A row that resolves to nothing stays in `RAW` and is counted; it is never given a made-up `account_id`.

## The contract check

Before a signal row leaves `RAW`: `source_url like 'https://%'` and `event_date is not null` and `evidence_tier in (1,2,3)` and (`quote is not null` or `evidence_tier = 3`). Failures go to `raw.ingest_rejects` with the reason, and the daily count is on the ops alert.

## n8n workflows (exports in `ingest/n8n/`)

| File | Trigger | Steps |
|---|---|---|
| `steadybase-delta.json` | Schedule, hourly | read cursor → POST `whats_new(since)` → insert rows → store `next_since` → if `truncated`, loop once |
| `clay-signal-webhook.json` | Webhook from Clay | validate → insert to `raw.clay_rows` if not present → enqueue account for scoring |
| `apollo-events.json` | Webhook from Apollo | insert `raw.apollo_events` → if `email_replied`, call the reply flow |
| `reply-flow.json` | Called by `apollo-events` | assemble thread → `reply.md` model call → write `core.outcomes` (class) → `decide()` via the agents service → post to Slack |
| `swarm-weekly.json` | Schedule, weekly | for each worked account, GET intro paths → insert `raw.swarm_paths` |
| `openai-batch.json` | Schedule, nightly (only when Cortex is unavailable in region) | build JSONL from `marts.batch_inputs` → upload → create batch → poll → write results |

Credentials are referenced by name. The exports are checked in with credential ids stripped.

## Acceptance

- [ ] On the fixture, every SteadyBase and Clay row lands in `RAW` with its dedupe key; re-running an hour produces zero duplicates.
- [ ] A planted row with `http://` is rejected and counted.
- [ ] A planted subsidiary row with the parent's domain lands in `core.review_queue` with reason `domain_collision`, not in `core.account`.
- [ ] The SteadyBase cursor survives a restart; no gap and no replay across the restart (compare `event_key` sets).
- [ ] Apollo reply webhook to Slack card in under 60 seconds end to end.
