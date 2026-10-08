# Decisions

Defaults taken where the design had a choice, with the reason, so a builder does not re-decide them. Open questions at the bottom. Add to "Changed during build" when reality disagrees with the spec.

## Taken

| # | Decision | Reason | Reversible? |
|---|---|---|---|
| 1 | **Models are OpenAI's.** GPT-5.5 for briefs, drafts, QA, replies; GPT-5 nano for classification, reason codes, prospect rows, orchestrator summaries. | Meridian Travel's preference. Prompts are Markdown with a `model:` frontmatter key, so a change is a one-line PR; no abstraction layer is built. | Yes, per prompt |
| 2 | **Build tool is Codex** (Claude Code works identically; both read the same conventions). | Same reason. | Yes |
| 3 | **Snowflake is memory. Clay is not.** | Clay charges per row touched; Snowflake is where you keep what you already paid for. SteadyBase's tenant views are already Snowflake-native. | No |
| 4 | **Batch work runs on Snowflake tasks and Cortex where the region allows; otherwise the OpenAI Batch API filed from one n8n flow.** Event flows run on n8n. Code is reserved for the Slack app, `decide()`, and evals. | Thousands of rows a night with no latency requirement is batch work. A one-person GTM engineering function should not run a fleet of workers. | Yes |
| 5 | **n8n, not Zapier.** | Zapier's per-task pricing at 100,000 touches a month exceeds the model bill, and it cannot host the Slack interaction endpoint. | Yes |
| 6 | **Identity: SteadyBase resolver for the public book, a domain-first ladder in Snowflake for the private book, one review queue.** Meridian Travel owns the id map. | The public book is a minority of accounts; the private ladder has to exist anyway; owning the map de-risks the vendor. | No |
| 7 | **Receipts are stored as URLs plus the verbatim quote**, never as vendor ids alone. | Signals must outlive the vendor. | No |
| 8 | **Scoring is SQL, weights v1 are judgment, refit at 300 attributable meetings.** | A formula can be audited and explained; the pilot cannot fit weights. | Yes |
| 9 | **Tier is from Salesforce `segment` and `strategic_flag`, not from employee count.** | Segment is what territories are drawn on; an employee-count rule would fight the CRM. | Yes |
| 10 | **`AUTO_GEOS = {US, CA}`; EU and UK never auto; DE and AT never email-first.** | Cold B2B email law differs by country; legal owns `core.geo_rules`. | Yes, by legal |
| 11 | **Replies come from Apollo's reply webhook and Centralize's email sync, never from reading rep inboxes.** | Scope, security review, rep trust. | Yes |
| 12 | **Slack App Home list for the playbook, DMs only for P1s and replies.** | Nine cards a day in a DM is a notification stream, not a work queue. | Yes |
| 13 | **Account-level holdout inside the pod, not a control pod.** | Same reps removes manager and territory confounds. | No, for the pilot |
| 14 | **No PII in prompts.** First name, title, persona, brief. | Privacy review, and the models don't need it. | No |
| 15 | **Business email only; the MoltSets personal-email endpoint is never called; no SMS.** | Compliance. | No |
| 16 | **Clay plays are built in the UI and exported as JSON for review.** "Plays as code" means reviewable, not programmatically recreated. | Clay's API pushes rows and receives webhooks; it does not build tables. | No |
| 17 | **Connectivity for reads, an operator for writes.** Agents and people read production through read-only roles and the vendor MCPs; every production write to `core.*` or the switches goes through the Navigator operator's preview, ticket, apply, verify gate (`ops/operator.md`). Salesforce and Apollo production writes go through the operators in gtm-ops-agents. No operator sits in the runtime send path. | The pipeline already has its gates as stages; the humans operating the pipeline need a gate too, and a flow tool cannot hold one. | Yes |

## Open

| # | Question | Who answers | Default until answered |
|---|---|---|---|
| A | What share of the book is public? | RevOps, from Salesforce | Assume 15%; Clay budget sized for the rest |
| B | Where does the SteadyBase pilot stop today? Do signals already land in Snowflake and Slack? | Head of GTM Ops | Assume views exist, nothing wired to reps |
| C | Is Meridian Travel's Snowflake on Azure (Cortex hosts OpenAI models) or AWS? | Data engineer | Assume AWS; batch through n8n and the OpenAI Batch API |
| D | Does Nooks expose an API for pushing call lists and pulling dispositions? | GTM engineer, with Nooks | CSV import for lists; dispositions from the Salesforce sync |
| E | Does Centralize expose an API, or is it native integrations only? | GTM engineer, with Centralize | Native Salesforce integration; handoff map is a Centralize link on the opp |
| F | Tier boundaries and `AUTO_GEOS` beyond US and CA. | Sales leadership and legal | As in `docs/tiers.md` |
| G | Which pod, and which manager. | Head of GTM Ops | |
| H | Voice guide and product-claims library: do they exist? | Enablement | QA uses a placeholder library in `evals/fixtures/claims.json` and flags every product claim |

## Changed during build

(empty; add entries as `YYYY-MM-DD, part, what the spec said, what was true, what was done`)
