# Navigator

An agent team that does the market, account, and prospect research, drafts and checks every touch, handles replies, and tells each of 500 BDRs what to do next. Designed for 500 reps, built to run at 1,000.

This repository is the **implementation spec**. It is written so that a GTM engineer and a coding agent (Claude Code or Codex) can build Navigator from it without re-deciding what it is. The demo that explains the design to a human lives at the page linked below; this repo is what gets handed to the agent on day one.

Status: **spec, not code.** The only executable pieces are the orchestrator's decision rules (`agents/orchestrator/decide.py`, with tests) and the scoring SQL (`data/scoring.sql`). Everything else is a specification with acceptance criteria.

## How to read this repo

| Read this | To learn |
|---|---|
| `CLAUDE.md` | The conventions every part follows, and the build order. Read first. |
| `PROMPT.md` | The kickoff prompt to paste into Claude Code or Codex. |
| `docs/architecture.md` | The five layers and what each component does. |
| `docs/data-flow.md` | What happens to a record at every hop, and how often. |
| `docs/scoring.md` | The score, term by term, with one account worked through it. |
| `docs/rules.md` | The orchestrator's rules of engagement, in words. The code is `agents/orchestrator/decide.py`. |
| `docs/tiers.md` | Autonomy by tier, caps, and the geography gate. |
| `docs/pilot.md` | Three weeks to a live pod, done criteria, the holdout design, and the metrics. |
| `docs/decisions.md` | Defaults taken where the design had a choice, and the open questions. |
| `data/` | Schema, scoring SQL, dbt layout. |
| `ingest/` | How each source lands in Snowflake. |
| `agents/` | The agent team: prompts, the orchestrator, evals hooks. |
| `slack/` | The Bolt app: cards, actions, App Home, manifest. |
| `plays/` | The five signal plays, one file each. |
| `ops/` | Secrets, caps, kill switch, cost meter, audit log, and the operator that gates production writes (`ops/operator.md`). |
| `integrations/` | One file per vendor: auth, endpoints used, payload shapes, limits, and what still needs verifying. |
| `evals/` | The golden set and how it runs. |

## The four rules

1. **Quote it as is or not at all.** Agents personalize only with receipts. For a public company that is a verbatim quote from a call or filing. For a private one it is the artifact itself: a job posting, a press release, a funding announcement. No artifact, no personalization; the touch runs on fit and timing.
2. **Research once, use many.** Account briefs live in Snowflake with a freshness date. Nothing is re-researched inside 14 days unless a new signal fires.
3. **Autonomy by tier.** SMB touches send on their own within caps and permitted geographies. Mid-market drafts wait for a rep. Enterprise gets research and warm paths, and a human writes.
4. **Outcomes retrain the score.** Every reply, meeting, and opp flows back. Weights are refit against what converted, and QA grades are checked against reply rates.

## The stack

Snowflake (memory and scoring), SteadyBase (receipted signals and identity for public companies), Clay (private-company signals and the enrichment waterfall), MoltSets and Apollo (contacts), TheSwarm (warm paths at list scale), Centralize (buying-committee coverage on live deals), Apollo and Nooks (execution), Salesforce (system of record), Slack (rep interface), OpenAI (models), n8n (event flows), Codex or Claude Code (build tool).

## Demo page

The human-facing walkthrough (architecture, a rep's morning, data flow, build plan, scale and cost) is a single HTML page kept at `demo/navigator.html` and published at jholm.co/navigator.

## License and data

Larkspur Dynamics and every person named in examples are fictional. Vendor descriptions are from public documentation as of September 2026 and may have changed; each `integrations/*.md` carries its own date.
