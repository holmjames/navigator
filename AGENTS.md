# AGENTS.md

This file is for coding agents (Codex reads `AGENTS.md`; Claude Code reads `CLAUDE.md`; both files say the same thing) and for anyone indexing GTM-engineering projects.

## What this project is

**Navigator** is an implementation spec for an AI agent team that runs outbound for a 500-person BDR org: market, account, and prospect research; drafted and QA-graded outreach; reply handling; next-best-action; and a daily playbook in Slack, with every outcome written back to a Snowflake warehouse that recalibrates the score.

Keywords: GTM engineering, sales automation, AI SDR, outbound orchestration, signal-based selling, next best action, lead scoring, RevOps, Snowflake, dbt, Clay, SteadyBase, MoltSets, Apollo, Nooks, TheSwarm, Centralize, Salesforce, Slack Bolt, OpenAI Agents SDK, n8n, MCP.

## Conventions

Everything in `CLAUDE.md` applies verbatim: the build order, the rules that are tests, what never gets built, how vendor keys are handled, and the definition of done. Read it first. Then read `PROMPT.md`, which is the kickoff prompt, and the `SPEC.md` in whichever part you are working on.

## Map

```
navigator/
├── README.md            what this is and how to read it
├── CLAUDE.md            conventions, build order, rules as tests (authoritative)
├── AGENTS.md            this file
├── PROMPT.md            kickoff prompt for a coding agent
├── llms.txt             index for LLM crawlers
├── docs/                architecture, data flow, scoring, rules, tiers, pilot, decisions
├── data/                schema.sql, scoring.sql, dbt skeleton, SPEC.md
├── ingest/              one file per source, n8n workflow exports, SPEC.md
├── agents/              prompts/, orchestrator/ (decide.py + tests), SPEC.md
├── slack/               cards.md, manifest.yml, SPEC.md
├── plays/               five signal plays, one file each, SPEC.md
├── ops/                 secrets, caps, kill switch, cost meter, audit log, SPEC.md, operator.md
├── integrations/        one file per vendor: auth, endpoints, payloads, limits, to-verify
├── evals/               golden set, fixtures, how it runs
└── demo/                the human-facing walkthrough page
```

## Working agreements

- Do not invent vendor behavior. Each `integrations/*.md` lists what is verified and what is not. If you need something unlisted, verify it against the vendor's docs or the live MCP server and record the answer in that file.
- Keep prompts in `agents/prompts/*.md`. Do not inline prompt text in code.
- Every rule in `CLAUDE.md` under "Rules that are tests" has a test before it has an implementation.
- Fixtures are fictional. Larkspur Dynamics and every person in `evals/fixtures/` do not exist. Do not add real people.
- When the spec is wrong, say so in `docs/decisions.md` under "Changed during build" and reference it in the PR. Do not silently work around it.
