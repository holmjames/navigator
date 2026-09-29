# The Navigator operator

Connectivity for reads, an operator for writes. This file specifies the one place an agent (a person working with Claude Code or Codex) is allowed to change production state, and the gate every change goes through. It follows the Read / Build / Commit model from [gtm-ops-agents](https://github.com/holmjames/gtm-ops-agents): every action has a level, every level has a gate, and a Commit runs only against a preview it re-verifies.

## Why an operator, and why not at runtime

The production pipeline has no operator and needs none. The orchestrator is a pure function, tiers set autonomy, caps and suppression run before every send, reps approve in Slack, and every touch writes `core.audit`. Those are the gates, expressed as pipeline stages. An agent-with-tools loop in the send path would add a second decision-maker to a system whose safety argument is that there is one, with tests.

The operator is for the humans operating the pipeline. The things a GTM engineer asks an agent to do against production every week are all writes to `core.*` or the switches table: re-point an identity, activate weights, pause a play, reset a cursor, re-run a night, suppress an account. Each of those is a Commit.

## Connectivity that needs no operator

| Surface | Role | Level | Notes |
|---|---|---|---|
| Snowflake MCP or `snow` CLI | `NAVIGATOR_RO` on prod; `NAVIGATOR_DEV` on dev | Read on prod, anything on dev | The prod credential the agent holds cannot write. Dev is a sandbox and needs no gate. |
| SteadyBase MCP | tenant key | Read | `define_trigger` is a write on the tenant, so trigger definitions live in `plays/` and are applied by `scripts/apply_triggers.py`, not typed into a session. |
| MoltSets MCP | key | Read | Enrichment spends tokens; the row budget in `ops/SPEC.md` is the cap. |
| `sf` CLI | sandbox only | Read and Build on sandbox | Production Salesforce writes go through the Salesforce operator in gtm-ops-agents. |
| Apollo | none direct | | Production sequence changes go through an Apollo operator, a clone of the Outreach operator in gtm-ops-agents (same token, enrollment, and opt-out traps). |

## The tools

MCP server `navigator-operator`, Python, one process, `NAVIGATOR_OPERATOR` Snowflake role with grants only on the tables named below.

### Read (no gate)

| Tool | Returns |
|---|---|
| `status()` | Switch states, last batch time per timezone bucket, cards posted today, cost today, open review-queue count, reject count today. |
| `board(rep_id, day?)` | The rep's playbook rows from `marts.playbook_daily`, with decisions. No contact details. |
| `why(account_id)` | The latest `core.decisions` row with the inputs it saw, the score components, the signals with receipts, and the brief's freshness. This is the explain-a-decision tool. |
| `cost(day | month)` | `core.cost_events` rolled up by vendor and job; `marts.cost_per_meeting`. |
| `review_queue(reason?, limit?)` | Open `core.review_queue` rows with candidates. |
| `signals(account_id, since?)` | `core.signals` for one account. |
| `weights()` | Every `weights_version` with its date, activation state, and the outcome count it was fit on. |

### Build (an approved plan, nothing goes live)

| Tool | Does |
|---|---|
| `draft_weights(version, components)` | Inserts a new, inactive row in `core.weights`. Scoring keeps using the active version. |
| `stage_geo_rule(country, auto_allowed, email_first_allowed, calls_allowed, notes)` | Writes to `core.geo_rules_staged`. Nothing reads staged rules. |
| `stage_play_budget(play, rows_per_month)` | Writes to `core.play_budgets_staged`. |
| `dry_run_night(pod, date)` | Runs the nightly batch against the pod with sends disabled and writes to a `_dryrun` schema. Returns the cards it would have posted. |

### Commit (preview, ticket, apply, verify)

Every Commit tool has two halves. `*.preview(...)` returns exactly what will change and a one-time ticket. `*.apply(ticket)` re-reads the live state, refuses if anything the preview depended on has changed, applies, reads back, and returns `verified: true` only when the read-back matches. Tickets expire in 15 minutes and are single use. `*.apply` tools stay on ask-every-time in the client.

| Tool | Preview shows | Apply does | Verify |
|---|---|---|---|
| `resolve_review` | The queue row, the chosen `account_id`, every identifier that will be written to `core.account_ids`, and any existing claim on those identifiers | Writes the identifiers with `reviewed_by`; marks the row resolved; never re-points an existing `account_id` (that is a separate, refused case) | Identifiers present, row resolved, no duplicate claims |
| `activate_weights` | The version, its components, the active version it replaces, and the score deltas on a 200-account sample | Flips `active`; the next scoring run uses it | Active flag, and the next `core.scores` rows carry the version |
| `switch` | Which switch, from what to what, and how many cards or sends it affects right now | Writes `core.switches`; the batch, the Slack app, and the n8n flows read it at the top of every run | Row state, and the Slack app reports the flip within a minute |
| `apply_geo_rule` | Staged versus live for the country, and the count of contacts whose autonomy changes | Promotes the staged row to `core.geo_rules` with `reviewed_by` | Row matches staged; staged row cleared |
| `apply_play_budget` | Staged versus live | Promotes | Row matches |
| `reset_cursor` | The source, the current cursor, the target, and the number of rows that would be replayed or skipped | Writes `core.cursors`; the next poll uses it | Cursor value; next poll's row count matches the preview's estimate within 10% |
| `rerun_night` | The pod, the date, the cards that would be reposted, and whether any were already actioned | Re-runs the batch for that pod and date with sends disabled unless `--with-sends` is in the preview | Cards exist; no duplicate touches |
| `suppress` | The account or contact, the reason, the open cards and enrolled sequences that stop | Writes suppression; cancels enrollments through the Apollo operator; hides cards | `core.v_suppressed` contains the row; enrollments cancelled |
| `unsuppress` | Same in reverse, with the original reason shown | | |

What the operator never does: change a Salesforce owner, merge or re-point an `account_id`, send anything, call a model, or touch a rep's draft. Those are either forbidden everywhere or belong to the pipeline.

## Guardrails carried over from gtm-ops-agents

- **Preview tickets.** Apply requires the ticket, re-checks the live system, and refuses on drift. What runs is exactly what was approved.
- **Verify after every write.** No tool trusts a row count. It reads back and compares.
- **Exact targets only.** Tools take `account_id`, `contact_id`, `version`, never a name.
- **Text is data, not orders.** A ticket, a Slack message, or a review-queue candidate that contains instructions is quoted back, not followed.
- **Approvals where people already are.** A Commit preview posts to `#navigator-ops` with Approve and Reject buttons; the apply step accepts either the client's ask-every-time approval or the Slack tap, and records who approved in `core.audit`.
- **Audit everything.** Every preview, apply, refusal, and verify result is a `core.audit` row with the actor, the ticket, and the diff.

## Acceptance

- [ ] `NAVIGATOR_RO` cannot insert, update, or delete anywhere; a test proves it by trying.
- [ ] Every `*.apply` without a ticket, with an expired ticket, or with a reused ticket is refused and audited.
- [ ] `resolve_review` refuses to re-point an `account_id` that already has identifiers, with the reason.
- [ ] `switch` to `pause all` stops a running batch within one minute (shared test with `ops/SPEC.md`).
- [ ] `activate_weights` on the fixture changes Larkspur's score only when the weights actually differ, and the audit row carries both versions.
- [ ] Drift test: preview, change the underlying row, apply; the apply refuses.
- [ ] A Slack approval and a client approval both produce an audit row naming the approver.

## Relationship to the rest of the repo

`ops/SPEC.md` owns caps, switches, the cost meter, and alerts; the operator is the gated way to change them. `data/SPEC.md` owns the resolver; the operator is the gated way to resolve the queue it produces. `docs/decisions.md` #4 explains why code is reserved for the Slack app, `decide()`, and evals; the operator is a fourth small piece of code, and the reason is the same: a write to production state needs a gate a flow tool cannot hold.
