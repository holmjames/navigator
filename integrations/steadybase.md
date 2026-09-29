# SteadyBase

Receipted signals, identity resolution, people (identity only), earnings calendar, and triggers for public companies. Verified against `https://steadybase.io/llms-full.txt` on 2026-09-28.

## Endpoints

| Surface | URL | Auth |
|---|---|---|
| MCP (Streamable HTTP, JSON-RPC 2.0, stateless) | `https://mcp.steadybase.io/mcp` | `Authorization: Bearer gtms_...` on every request; missing key returns JSON-RPC `-32001` |
| REST | `https://api.steadybase.io` (`/v1/accounts`, `/v1/whats_new`, `/v1/upcoming`, `/v1/search`, `/v1/accounts/bulk`, `POST /v1/accounts/resolve`) | same |
| Snowflake | Tenant views `GTM_SIGNALS.TERRITORY.V_TENANT_WHY_NOW`, `V_TENANT_ACCOUNT_SIGNALS`, `V_TENANT_PEOPLE`, `V_TENANT_FUTURE_EVENTS`, `V_TENANT_TRIGGERS`, `V_TENANT_TRIGGER_HITS`, read as role `GTM_SIGNALS_RO_<TENANT>` | Snowflake role |

Keys are issued by hand (`andrew@steadybase.io`). A key reads the shared corpus on day one; book answers need the tenant onboarded (`tools/onboard_tenant.py` on their side) and a board published. Entitlement `navan_read`: contact data is off; people come back as name, title, persona, LinkedIn URL only.

## Tools Navigator uses

| Tool | Used for | Notes |
|---|---|---|
| `whats_new(since, limit)` | The delta feed. Every signal first seen since the cursor, newest first, with `event_key`, `quote`, `why_it_matters` (derived, never quotable), `source_url`, `page_ref`, `receipt`, `evidence tier`, `call_first`. | Pass the previous `next_since` back as `since`. `truncated=true` means the page is the oldest slice; poll again at once. Retention 30 days. `feed="events"` gives the live event log (`trigger_hit`, `live_alert`, `clip_ready`, `account_changed`) with an `event_seq` cursor. |
| `bulk_since(cursor, kinds)` | Everything new on the book since an ISO cursor: transcripts, documents, signals, trigger hits, people first seen. | Cursor exclusive; older than 90 days refused, backfill with `bulk_company`. |
| `bulk_company(ticker or account_id)` | Everything on one account in one call: identity, identifiers, family, people, signals, transcripts, documents, events, trigger hits. | Caps per list, default 200. |
| `pg_account_signals(ticker, account_id, since_days, signal_type, q)` | Signals on one account, or across the whole book with no ticker. Lanes: `cost, cost_cutting, efficiency, expansion, geo, headcount, hiring, vendor_change, budget_spend, initiative, guidance, leadership_change, sec_filing, pain_point, other`. | `signal_type=cost, q=travel` is the T&E cost question. |
| `pg_people(ticker, persona, new_in_role_days, limit, cursor)` | Committee by persona; new-in-role finance leaders across the book. | Never returns email or phone. One row per person per persona. |
| `pg_future_events(days)` / `next_earnings_call(ticker)` | Earnings calendar with confirmed times, webcast URLs, capture status. | Feeds `next_earnings_call_date` and the quiet-period rule. |
| `pg_deals(ticker, status, since)` | M&A from filings with the receipt sentence. | |
| `find_companies(resolve={...})` | The identity resolver. Identifiers: `account_id, cik, lei, ticker, exchange_ticker, domain, linkedin_company, legal_name (+country/state), parent_hint, duns`. Returns `resolved`, `method`, `confidence`, `corroborated_by`, the corporate tree, the evidence list; or `ambiguous`, `conflict`, `no_match` with candidates. | Two candidates is never a match. `external_id` + `external_system` maps a Salesforce 18-char id. `bulk=true` pages the account universe (identity only). |
| `define_trigger(name, criteria_text, scope, filters)` / `list_triggers` / `trigger_hits` / `run_trigger_now` | Plain-language triggers compiled once and run hourly; hits carry the verbatim quote, receipt URL, char offsets, judge verdict. | Delivery to Slack, webhooks, and the `whats_new` feed. |
| `get_receipt(url)` | Reads the quoted span from a licensed transcript by `transcript_id`, `start`, `end`. | For verification before repeating a quote. |
| `search(query, kinds, since_days, tickers)` / `search_transcripts_local` / `search_company_signals(query, lane)` | Full-text search over the book's transcripts, documents, people, companies; and the public cross-company index. | `search_company_signals` is public and cannot tell you what is on your book. |

## Identity ladder (confidence of a lone hit)

`account_id` 1.00, `lei` 1.00, `cik` 1.00, `duns` (customer-supplied only) 0.97, `exchange_ticker` 0.97, `ticker` 0.95, `domain` 0.92, `linkedin_company` 0.92, `legal_name + jurisdiction` 0.85, `former_name` 0.80, `ex21_parent` 0.80, `legal_name` alone 0.60 (weak, never a match by itself). Each agreeing rung adds 0.03. Coverage as of 2026-09-19: 10,140 resolved companies (5,321 public filers plus 4,819 subsidiaries); 209,093 EX-21 evidence nodes served only on request and never as a match.

## Quoting rules (theirs, adopted as ours)

- Quotable: `signals[].quote` with that row's receipt. Not quotable: `why_it_matters` (always derived), board-row headline quotes when `quote_is_quotable` is false, anything on `get_priorities` rows.
- "Quote it as is or not at all."

## From Clay

HTTP API enrichment, `POST https://mcp.steadybase.io/mcp`, body `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"pg_account_signals","arguments":{"ticker":"{{Ticker}}","signal_type":"cost","q":"travel","limit":5}}}`. The tool's JSON is a string inside `result.content[0].text`; parse it, map `rows[].SUMMARY` to the quote column and `rows[].SOURCE_URL` to the receipt column, and keep them next to each other. One call per row; use `bulk_since` for whole-book pulls.

## Coverage and risk

- Shaped around SEC filers. Expect it to cover a minority of a 500-rep book. Clay carries the private lane.
- The docs read like a very small company (keys by hand, draft pricing, "Needs Andrew" notes). Mitigations in `docs/decisions.md` #6 and #7: Navan owns the id map in its own Snowflake, the ladder is reproducible, receipts are stored as URLs plus the verbatim quote, and nothing downstream depends on the MCP being up.

## Pricing (draft on their page, 2026-09-28)

Public: free, no key. Build: $99/month, one tenant key, all 48 MCP tools, flat rate. Operate: custom, adds ICP, personas, private books, account-scoped triggers. Navan's tier is Operate.

## To verify

- [ ] Whether Navan already has a tenant, a key, and a published board (`GET /v1/accounts?limit=1` answers 200 with rows).
- [ ] Whether the tenant views are shared into Navan's Snowflake account, and which role reads them.
- [ ] Slack delivery channel for triggers.
