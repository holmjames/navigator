# Architecture

Five layers. Data enters at the top, a rep acts at the bottom, and outcomes loop back to the second layer.

```
Signals and data      SteadyBase | Clay | MoltSets, Apollo | TheSwarm | Salesforce
        |               signals with receipts, contacts, warm paths, CRM state
Identity and memory   Resolver -> Snowflake (accounts, contacts, signals, briefs, touches, outcomes, scores)
        |               resolved accounts, cached briefs, scores with reasons
Agent team            Market | Account | Prospect | Scoring | Messaging | QA | Reply | Next best action
        |               approved drafts, call lists, intro requests, tasks
Execution             Apollo | Nooks | Centralize | Salesforce
        |               playbooks, cards, approvals, coverage
Rep interface         Slack bot | Manager view
        ^
        +---- outcomes (opens, replies, calls, meetings, opps) back to Snowflake
```

## Layer 1: signals and data

| Component | Job | Takes in | Sends on | Why this one | If it isn't there |
|---|---|---|---|---|---|
| **SteadyBase** | Receipted signals for the public-company part of the book. Every signal is a verbatim quote from an earnings call, filing, deck, or job posting with a link to where it was said. | The book (tickers, domains), plain-language triggers, the persona ladder (CFO, controller, FP&A, treasury, AP, procurement, travel manager). | Trigger hits with quotes and receipts, a ranked why-now list, P1 to P4 priorities, next earnings call per account, finance leaders new in role, M&A from filings. Delivered as Snowflake views, Slack, webhooks. | Its public docs are written around a Meridian Travel travel book. Receipts make automated outreach safe. Shaped around SEC filers, so it covers a minority of a 500-rep book; Clay carries the rest. Never returns email or phone. | Clay research plus an earnings-transcript API approximates the signals without the receipts or the identity layer. |
| **Clay** | The private and mid-market lane, and the enrichment waterfall for every account. | Account lists from Snowflake; job postings, funding, office openings, tech detection (Concur, Spendwell, Harbor Card, Kestrel, TravelPerk); Claygent research; SteadyBase, MoltSets, TheSwarm over HTTP. | Enriched rows to Snowflake and Salesforce; a webhook to the pipeline on a new signal. | Fastest way to stand up five plays without engineering time. Per-row pricing is managed by research-once and search-time suppression. | The same plays in code against provider APIs; slower to build, cheaper at 1,000 reps. |
| **MoltSets** | Verified business email (with a risk grade) and carrier-verified mobile. | Name plus domain, or LinkedIn URL, from SteadyBase people and Clay. A suppression list of domains. | Email, grade, validation date, mobile, into Snowflake and Apollo. | Flat plans, API-first, MCP-native; suppression applied at search time costs nothing. Closed beta. | Apollo behind it on every row. |
| **Apollo (data)** | Contact fallback and a second opinion on titles. | Whatever MoltSets couldn't verify. | Contacts into Snowflake and its own sequences. | Already on the table. | ZoomInfo or Cognism. |
| **TheSwarm** | Warm paths at list scale, before contact: who at Meridian Travel, or among its customers, investors, advisors, knows someone on the committee. | Account domains; work and education overlaps mapped passively; LinkedIn and email connections with opt-in. | Intro paths with a strength score, job-change alerts, into Clay and Snowflake. | Runs on the whole book in bulk. The relationship term in the score comes from here. Coverage grows with employee opt-in. | Centralize finds team-network intros deal by deal; without either, the relationship term is zero. |
| **Salesforce (data)** | What Meridian Travel already knows: ownership, past opps, open deals, customers, do-not-contact. | Nothing new; it is the source. | Nightly sync into Snowflake; the 18-character ids the resolver maps to `account_id`. | Every signal has to land on the record the rep owns. | None. |

## Layer 2: identity and memory

| Component | Job | Detail |
|---|---|---|
| **Identity resolver** | One stable `account_id` per company across ticker changes, renames, subsidiaries. Territories, dedupe, and ownership key off it. | Public book: SteadyBase's ladder (LEI, CIK, exchange ticker, ticker, domain, LinkedIn, legal name plus jurisdiction) and its Salesforce id map. Private book: the same ladder on domain, LinkedIn slug, and legal name, run in Meridian Travel's own Snowflake. Two candidates is ambiguity, never a match; ambiguous and conflicting rows go to `core.review_queue`. Meridian Travel owns the id map either way. See `docs/data-flow.md` and `data/SPEC.md`. |
| **Snowflake** | Memory: account universe, every signal, the brief cache with freshness, every touch, every outcome. Deterministic scoring as SQL. | Takes SteadyBase tenant views, Clay results, MoltSets and TheSwarm output, Apollo and Nooks activity, Salesforce nightly. Sends the daily playbook per rep, scores with reason codes, manager metrics, and the training set for recalibration. Cortex writes reason codes without moving data out (OpenAI models on Azure-region accounts; see `integrations/snowflake.md`). |

## Layer 3: the agent team

Models are OpenAI's: GPT-5.5 for briefs, drafts, QA, and replies; GPT-5 nano for classification, reason codes, prospect rows, and the orchestrator's summaries. Nightly jobs run on the batch API. Prompts are in `agents/prompts/`.

| Agent | Cadence | Job |
|---|---|---|
| Market research | Weekly, per segment and territory | What moved, who reports this week, which plays are converting. A Monday brief to each pod's channel. |
| Account research | Per account, cached 14 days or until a new signal | The one-page brief: why now (with receipts), estimated travel footprint and drivers, current T&E stack, timing, risks, suppression check. |
| Prospect research | Per person on the committee | Persona, time in role, what they own, recent public posts. A persona-tagged contact row with a verified channel. |
| Scoring | Nightly and on every new signal | A formula in SQL (`data/scoring.sql`). The model only writes the three reason lines. |
| Messaging | Per touch | Email, call opener, LinkedIn note, in Meridian Travel's voice, for the persona. Personalizes only with receipts. |
| QA | Before any send | Grade A+ to F. Claim-to-receipt check, length, one ask, no links, voice. Below B goes back for a rewrite. |
| Reply | On inbound | Classifies (interested, objection, not now, out of office, referral, unsubscribe, wrong person, question), drafts the answer, updates state, stops the sequence. |
| Next best action | Per account, on score or signal change | The orchestrator. Suppression, caps, geography, freshness, then warm intro, email, call, LinkedIn, wait, route to AE, or disqualify. `agents/orchestrator/decide.py`. |

## Layer 4: execution

| Component | Job |
|---|---|
| **Apollo (sequences)** | Sends email at scale, enforces caps and unsubscribes, catches replies and bounces. Replies go to the reply agent by webhook. |
| **Nooks** | Dialer. Call lists from the orchestrator, call prep from the brief, transcripts and dispositions back to Snowflake. API availability is unverified; see `integrations/nooks.md`. |
| **Centralize** | Once an account is live: buying-committee map, who is engaged, who is missing, warm intros through the team, next move. Handoff map for BDR to AE. API availability is unverified; see `integrations/centralize.md`. |
| **Salesforce (record)** | Tasks, events, activity, stage changes, from every layer. Nightly to Snowflake. |

## Layer 5: rep interface

| Component | Job |
|---|---|
| **Slack bot** | Morning playbook in an App Home list; DMs for P1s and replies. One card per account: brief, score with reasons, draft with grade, next action, buttons (approve, edit, call now, snooze, disqualify). |
| **Manager view** | Signals fired, share actioned within 24 hours, reply and meeting rate by play and tier, QA grade versus reply rate, cost per meeting. |

## Operating it

People and coding agents read production through read-only roles and the vendor MCPs. Every production write goes through the Navigator operator (`ops/operator.md`): preview, one-time ticket, apply with a drift check, read-back verify, audit. Nothing at runtime uses it; it is for the humans operating the pipeline.

## The loop

Replies, meetings, and opps update `core.outcomes`, joined to the touch and the signal that started them. Weights are refit against what converted (quarterly at 500 reps; the pilot cannot fit weights). QA grades are checked against reply rates so the grader is graded.
