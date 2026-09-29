# Data flow

Three things the design argues for: every row is resolved to one `account_id` before it is stored, agents read the cache before they research, and outcomes return to the same tables the score is computed from.

## Hop by hop

| Stage | What happens | Cadence |
|---|---|---|
| **Collect** | SteadyBase signals arrive as shared Snowflake views and as a delta feed polled on a cursor (`whats_new(since=...)` and `bulk_since(cursor=...)`; nothing replayed, nothing skipped). Clay pushes enriched rows to its Snowflake destination and fires a webhook when a play matches. Salesforce syncs nightly through the native connector. Apollo and Nooks post events as they happen. TheSwarm paths refresh weekly per worked account. | Hourly, nightly, live |
| **Resolve** | Each account row is matched to one `account_id` through the identifier ladder and to its Salesforce id. Contacts key on `(account_id, linkedin_url)`. Ambiguous or conflicting rows go to `core.review_queue`; nothing is guessed. A subsidiary carrying its parent's website is caught here. | On arrival |
| **Store** | `RAW` tables are append-only and keep the source URL on every signal. dbt builds `CORE` and the `MARTS` the playbook and manager view read. A signal without an `https://` source URL never leaves `RAW`. | Hourly builds |
| **Score** | `data/scoring.sql` computes fit, signal, timing, relationship. Tier follows from segment and country; priority from the score. GPT-5 nano writes three plain-language reasons from the components. | Nightly, and on every new signal |
| **Decide** | The orchestrator wakes for an account when its score or signals change. It checks suppression, caps, geography, and brief freshness. Only then do agents run, and only the ones needed. | Event-driven |
| **Research and draft** | Account research writes or refreshes the brief. Prospect research fills the committee with a verified channel and a warm path. Messaging drafts from receipted facts only. QA grades; below B goes back. Agents read the cache first and call vendors only for what is missing. | Per account, cached 14 days |
| **Act** | A card lands in Slack. Tier A sends within caps in permitted geographies. Tier B waits for a tap. Tier C gets research and a warm path only. Taps become Apollo enrollments, Nooks calls, TheSwarm intro requests, Centralize maps, Salesforce tasks. | 7 AM local, then live |
| **Learn** | Opens, replies, dispositions, meetings, opps are written to `core.outcomes`, joined to the touch and the signal. Weights are refit against what converted; QA grades are checked against reply rates. | Live capture, quarterly refit |

## Rules for the data

1. **Receipted or not stored.** A signal without a source URL is rejected at ingest and counted in `core.ingest_rejects`. The quote is stored verbatim; the model never paraphrases it into outreach.
2. **Dedupe on `account_id` and nothing else.** Ticker and domain are joins of convenience. Two rows sharing an id is a bug to fix upstream, not a merge for a rep to notice.
3. **Contact data stays in the data layer.** Email and mobile live in Snowflake and Apollo. A prompt gets a first name, a title, a persona, and the brief. It never sees a phone number or an email address.
4. **Suppression runs twice.** At search time (`core.v_suppressed` becomes the exclude list for MoltSets and Clay, so suppressed people are never bought) and immediately before any send.
5. **Briefs expire.** `fresh_until` is the earlier of 14 days after `written_at` and the newest signal's `first_seen`. A stale brief is rebuilt before a rep sees it.
6. **Every touch carries its `draft_id` and `qa_grade`.** A reply can always be traced to the exact words that earned it.
7. **Geography gates autonomy.** Every contact carries a country. Tier A applies only in `AUTO_GEOS`; EU contacts are always human-approved; mobiles are scrubbed against do-not-call lists before any call list is built.
8. **Retention follows Navan's CRM policy.** Vendor DPAs cover SteadyBase, MoltSets, TheSwarm, and Centralize. Nooks transcripts keep the same retention as the call recorder already in place.

## Idempotency

- SteadyBase rows dedupe on `event_key` (the same identity its Slack and webhook lanes use). A pushed alert and a pulled row for one signal are one row.
- Clay rows dedupe on `(source, source_row_id)`.
- Apollo and Nooks events dedupe on the vendor's event id.
- The nightly batch is keyed on `(account_id, job, as_of_date)`; rerunning a night is safe.

## Tables

The full DDL is `data/schema.sql`. The core tables, trimmed to the columns that carry the design:

| Table | Key columns |
|---|---|
| `core.account` | `account_id`, `sfdc_id`, `name`, `domain`, `ticker`, `country`, `employees`, `segment`, `tier`, `owner_id`, `owner_type`, `parent_account_id`, `is_customer`, `has_open_opp`, `strategic_flag` |
| `core.account_ids` | `account_id`, `id_type` (lei, cik, ticker, exchange_ticker, domain, linkedin_company, legal_name, sfdc_id), `id_value`, `source`, `confidence` |
| `core.contact` | `contact_id`, `account_id`, `linkedin_url`, `first_name`, `last_name`, `title`, `persona`, `seniority`, `role_start`, `country`, `email`, `email_grade`, `email_validated_at`, `mobile`, `mobile_verified_at`, `source`, `dnc` |
| `core.signals` | `signal_id`, `account_id`, `signal_type`, `quote`, `source_url`, `page_ref`, `event_date`, `evidence_tier` (1 quote, 2 artifact, 3 inferred), `verified`, `source`, `event_key`, `first_seen` |
| `core.briefs` | `account_id`, `brief_json`, `why_now`, `sources` (array of `signal_id`), `written_at`, `fresh_until`, `model`, `tokens_in`, `tokens_out` |
| `core.scores` | `account_id`, `as_of`, `fit`, `signal`, `timing`, `relationship`, `score`, `priority`, `reasons` (array), `weights_version` |
| `core.touches` | `touch_id`, `account_id`, `contact_id`, `channel`, `draft_id`, `qa_grade`, `tier`, `autonomy`, `sent_by` (agent, rep), `sent_at`, `sequence_id`, `signal_id` |
| `core.outcomes` | `outcome_id`, `touch_id`, `kind` (open, reply, call, meeting, opp), `class` (for replies), `at`, `detail` |
| `core.warm_paths` | `account_id`, `contact_id`, `connector_id`, `overlap` (work, school, investor), `strength`, `refreshed_at` |
| `core.review_queue` | `row_id`, `source`, `reason` (ambiguous, conflict, no_match, domain_collision), `candidates` (array), `resolved_by`, `resolved_at` |
| `core.cost_events` | `at`, `vendor`, `endpoint`, `account_id`, `rows`, `tokens_in`, `tokens_out`, `cost_usd`, `job` |
