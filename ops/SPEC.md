# ops/ — secrets, caps, kill switch, cost meter, audit

**Owns:** vendor keys and where they live; the caps and their enforcement points; the three kill switches; the cost meter; the audit log; alerts.

Production changes to any of these go through the Navigator operator: `operator.md`.

## Secrets

- Every vendor key lives in the secret store Meridian Travel already uses (AWS Secrets Manager or equivalent), read into environment variables at process start. Never in a file, a Clay cell, an n8n node's parameters (use n8n credentials), a fixture, a test, or a log line.
- Clay's HTTP enrichment columns reference keys from Clay's own secret store, not the cell.
- The SteadyBase key is rotated on any suspected exposure (their rotate-first, revoke-later policy gives seven days).
- A test greps the repo, the exported Clay tables, and the n8n workflow JSON for `gtms_`, `ms_`, `sk-`, and `Bearer ` followed by a token shape, and fails CI on a hit.

## Caps

| Cap | Value | Enforced by |
|---|---|---|
| Sends per rep per day | 40 | `decide()`; Apollo sequence setting (the lower wins) |
| Touches per contact per week | 2 | `decide()` |
| Tier-A auto sends per play per day, all reps | 1,500 | `ops` counter; exceeding pauses the play |
| New contacts bought per day | 5,000 | `ops` row budget on MoltSets and Apollo calls |
| Claygent runs per play per month | per play file | Clay table row limit plus `ops` counter |
| Model spend per day | $400 (500 reps) | `ops` counter; exceeding pauses the nightly batch and pages the GTM engineer |

## Kill switches

`core.switches` rows (`tier_a`, `play:<name>`, `all`) read by the nightly batch, the Slack app, and the n8n flows at the top of every run. Set by `/navigator pause ...` and `/navigator resume ...` (see `slack/SPEC.md`). Every change writes `core.audit`. A paused `all` leaves cards visible with buttons disabled and a banner.

## Cost meter

Every external call writes one `core.cost_events` row: `vendor`, `endpoint`, `job`, `account_id`, `rows`, `tokens_in`, `tokens_out`, `cost_usd`. Prices live in `ops/prices.yml` with a date, so a price change is a PR. `marts.cost_per_meeting` is the number on the manager view. The demo page's cost calculator is the same arithmetic at list prices.

## Audit log

`core.audit` records: every send (with `touch_id`, `draft_id`, `qa_grade`, `sent_by`), every switch change, every disqualify with reason, every review-queue resolution, every prompt version change (the git SHA). Retention follows CRM policy.

## Alerts (to the `#navigator-ops` Slack channel)

- Nightly batch did not finish by 06:30 local for any timezone bucket.
- Any cap exceeded.
- Any vendor returning errors above 5% for 10 minutes.
- Any day where `raw.ingest_rejects` grows by more than 2% of rows ingested.
- Review queue above 500 open rows.
- Model spend above 80% of the daily cap.

## Acceptance

- [ ] The secrets grep test exists and CI fails on a planted key.
- [ ] `/navigator pause all` stops the batch mid-run within one minute and the next run starts clean.
- [ ] `core.cost_events` reconciles to within 5% of the OpenAI and Clay usage dashboards for a test day.
- [ ] Each alert fires in a staged failure.
