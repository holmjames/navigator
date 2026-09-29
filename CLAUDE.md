# CLAUDE.md

Conventions for any coding agent working in this repo. Read this before touching anything. If a SPEC.md and this file disagree, this file wins; say so in the PR.

## What Navigator is

A pipeline plus a small agent team that turns signals about companies into a daily, scored, drafted, QA-checked playbook for 500 BDRs, delivered in Slack, executed through Apollo, Nooks, and Salesforce, with outcomes written back to Snowflake. `docs/architecture.md` has the picture; `docs/data-flow.md` has the hops.

## Build order

Build in this order and do not skip ahead. Each step has a done test in its SPEC.md.

1. `data/` schema and dbt skeleton. Load the synthetic book in `evals/fixtures/`.
2. `ingest/` for Salesforce and one signal source (SteadyBase if a key exists, otherwise Clay). Rows must pass through the resolver.
3. `data/scoring.sql`. Larkspur must score 91 (`docs/scoring.md` shows the arithmetic).
4. `agents/orchestrator/` (already has tests; make them pass against real tables).
5. `agents/prompts/` wired to the nightly batch: briefs, drafts, QA, reasons.
6. `slack/` cards and actions.
7. `ingest/` for Apollo and Nooks events, the reply flow, outcomes.
8. `ops/` caps, kill switch, cost meter, audit log.
9. Everything else.

## Rules that are tests, not guidelines

Write these as tests before the code that could violate them exists.

- **Receipted or not stored.** A row in `core.signals` must have a non-null `source_url` beginning with `https://`. The ingest layer rejects anything else and counts it.
- **Quote it as is or not at all.** A draft may include a quote only if it is a verbatim substring of a `signals.quote` for that account. QA fails any draft that paraphrases a quote inside quotation marks.
- **No artifact, no personalization.** If an account has no signal with `evidence_tier <= 2`, the draft uses the fit-and-timing template and the card says so.
- **Dedupe on `account_id` and nothing else.** No code path merges on ticker, domain, or name. A domain collision goes to `core.review_queue`.
- **No PII in prompts.** The prompt assembly function is the only thing that builds model inputs. It passes first name, title, persona, and the brief. It never passes email, phone, or LinkedIn URL. There is a test that greps assembled prompts for `@` and digit runs.
- **Suppression twice.** `core.v_suppressed` is checked at search time (as `exclude_company_domain` to MoltSets and Clay) and immediately before any send.
- **Geography gates autonomy.** `decide()` returns `autonomy = "auto"` only when `country in AUTO_GEOS`. EU contacts are always `approve` or `research_only`.
- **Caps are enforced in two places.** In `decide()` and in Apollo's sequence settings. If they disagree, the lower one wins.
- **Every touch carries `draft_id` and `qa_grade`.** A send without both is a bug.
- **Briefs expire.** `fresh_until` is 14 days from `written_at` or the newest signal's `first_seen`, whichever is earlier. The playbook never shows a stale brief.

## What never gets built

- A second CRM. Salesforce is the system of record. Navigator writes tasks, events, and opp stage changes through the API and reads everything else nightly.
- A model abstraction layer. The models are OpenAI's (see `docs/decisions.md`). Prompts live in `agents/prompts/` as Markdown with a frontmatter block naming the model, so a model change is a one-line PR.
- Custom scheduling infrastructure. Batch work runs on Snowflake tasks (Cortex where the region allows it, otherwise the OpenAI Batch API filed from one n8n flow). Event flows run on n8n. Code is reserved for the Slack app, the orchestrator's decision function, evals, and the operator. `docs/decisions.md` explains.
- An agent-with-tools loop in the send path. Nothing at runtime decides what to call; the orchestrator decides, the agents write words, the operator (`ops/operator.md`) is for people changing the pipeline, not for the pipeline.
- Anything that reads a rep's inbox directly. Replies arrive from Apollo's reply webhook and from Centralize's email sync.

## Vendors from the CLI

Two vendors expose MCP servers, and you should use them while building, both to read real data and to check your assumptions:

```
claude mcp add --transport http steadybase https://mcp.steadybase.io/mcp --header "Authorization: Bearer $STEADYBASE_KEY"
claude mcp add --transport http moltsets  https://mcp.moltsets.com/mcp    --header "Authorization: Bearer $MOLTSETS_KEY"
```

(Check `integrations/moltsets.md` for the exact MCP URL; the REST base is `https://api.moltsets.com/api/v1/tools` and every request needs a `User-Agent` header.)

Keys come from the environment only. Never write a key into a file, a fixture, a test, a log line, or a commit. If you see one in the repo, stop and say so.

Snowflake: use the `snow` CLI with the `NAVIGATOR_DEV` role on dev, and `NAVIGATOR_RO` on prod. Production writes to `core.*` and the switches go only through the Navigator operator (`ops/operator.md`), whose `*.apply` tools stay on ask-every-time; production Salesforce and Apollo writes go through the gtm-ops-agents operators. If you find yourself typing an `update` against prod, stop. Salesforce: the `sf` CLI against the sandbox. dbt: `dbt run --select <model>`. Slack: the app manifest in `slack/manifest.yml`.

## Conventions

- Python 3.12, `uv` for environments, `ruff` for lint, `pytest` for tests. Type hints on public functions.
- SQL is Snowflake dialect. Schemas: `RAW`, `CORE`, `MARTS`. Tables are snake_case, singular for entities (`core.account`), plural for events (`core.touches`). Every table has `_loaded_at`.
- Prompts are Markdown files with YAML frontmatter (`model`, `temperature`, `max_output_tokens`, `output_schema`). The loader in `agents/prompts/loader.py` is the only thing that reads them.
- One n8n workflow per file in `ingest/n8n/`, exported JSON, checked in. Credentials are referenced by name, never embedded.
- Every external call logs `{vendor, endpoint, account_id, rows, tokens_in, tokens_out, cost_usd}` to `core.cost_events`. The cost meter is not optional.
- Commits: one part per PR, tests in the same PR. Commit messages say what changed and why in one line, then the SPEC section it satisfies.

## Definition of done, per part

A part is done when its SPEC.md acceptance list passes, its tests run in CI, the cost meter shows its calls, and the Friday demo for its week (see `docs/pilot.md`) can be run from a clean environment using only `README.md` and `PROMPT.md`.

## When something in the spec is wrong

It will be. When a SPEC.md conflicts with a vendor's actual API, a table can't hold what a prompt needs, or a rule in `docs/rules.md` can't be implemented as written, do not silently work around it. Open a short entry in `docs/decisions.md` under "Changed during build" with the conflict, the choice, and the date, and reference it in the PR.
