# Kickoff prompt

Paste this into Claude Code or Codex from the repo root. It assumes the environment has `snow`, `sf`, `dbt`, and `uv` installed, keys in the environment, and the SteadyBase and MoltSets MCP servers added (see `CLAUDE.md`).

---

You are implementing Navigator, an AI agent team that runs outbound for a 500-rep BDR organization. This repository is the spec. Nothing about what Navigator is remains to be decided; what remains is building it in the order the spec gives, with the tests the spec names.

Start by reading, in this order: `CLAUDE.md`, `AGENTS.md`, `docs/architecture.md`, `docs/data-flow.md`, `docs/scoring.md`, `docs/rules.md`, `docs/tiers.md`, `docs/decisions.md`. Then read the `SPEC.md` for the part you are about to build, and the `integrations/*.md` files it references.

Then confirm the environment: run `uv run pytest -q` and report the result (47 tests should pass before you write anything). Run `snow sql -q "select current_region(), current_version()"` and record the region in `docs/decisions.md` open item C, because it decides whether batch model calls run inside Snowflake or through the OpenAI Batch API. Call `list_lanes` on the SteadyBase MCP server and `search_people` with `limit: 1` on MoltSets to prove both keys work; do not print the keys or the responses' contact fields.

Build in the order in `CLAUDE.md`, one part per pull request, tests in the same PR:

1. `data/`: apply `schema.sql` to the dev database, load `evals/fixtures/`, build the dbt skeleton, implement `resolve_private`, and make `scoring.sql` produce 91 for `acc_larkspur` with components 37/32/12/10 (the Python reference in `data/scoring_reference.py` is the oracle). Acceptance list is in `data/SPEC.md`.
2. `ingest/`: Salesforce through the connector, then one signal source (SteadyBase if the key has a book, otherwise Clay), every row through the resolver, the contract check, the reject counter, the delta-feed cursor. Acceptance in `ingest/SPEC.md`.
3. `agents/`: the prompt loader and `assemble()` with its PII test, the nightly batch runner against the fixture book, QA's rewrite loop, reason codes. `decide()` already exists and its tests pass; wire it to real tables without changing its rules. Acceptance in `agents/SPEC.md`.
4. `slack/`: the Bolt app from `slack/manifest.yml` and `slack/cards.md`. Acceptance in `slack/SPEC.md`.
5. `ingest/` again: Apollo and Nooks events, the reply flow, outcomes.
6. `ops/`: caps, switches, the cost meter, the audit log, alerts.
7. `plays/`: build the five Clay tables in the UI from the play files, export them to `plays/exports/`, define the SteadyBase triggers.

Rules you follow without being reminded:
- The rules under "Rules that are tests" in `CLAUDE.md` get a failing test before they get an implementation.
- No key, token, or contact detail ever appears in a file, a log line, a fixture, or a commit.
- Prompts stay in `agents/prompts/*.md`. Do not inline prompt text.
- Every vendor call writes a `core.cost_events` row.
- When the spec is wrong about a vendor, a table, or a rule, do not work around it silently. Write the conflict, the choice, and the date under "Changed during build" in `docs/decisions.md`, reference it in the PR, and continue.
- Do not build a model abstraction layer, a second CRM, or custom scheduling infrastructure. `docs/decisions.md` explains each.

For each part, finish by running its acceptance list and the full test suite, then write a short PR description: what was built, which SPEC sections it satisfies, what was changed in `docs/decisions.md`, and what the Friday demo for this week can now show (`docs/pilot.md`).

Begin with the environment confirmation, then `data/`.
