# agents/ — the agent team

**Owns:** the orchestrator (`orchestrator/decide.py`), the prompts (`prompts/*.md`), the prompt loader and assembler, the nightly batch runner, the reply flow's model steps, and the evals hooks.

**Reads:** `core.*`, `marts.playbook_daily`.
**Writes:** `core.briefs`, `core.drafts`, `core.scores.reasons`, `core.decisions`, `core.outcomes` (reply class), `core.cost_events`.
**Called by:** Snowflake task (nightly), n8n reply flow, `slack/` (regenerate after edit).

## Models

| Job | Model | Mode | Prompt |
|---|---|---|---|
| Account brief | GPT-5.5 | batch, nightly | `prompts/brief.md` |
| Prospect row | GPT-5 nano | batch, nightly | `prompts/prospect.md` |
| Draft (email, opener, LinkedIn) | GPT-5.5 | batch, nightly | `prompts/draft.md` |
| QA grade | GPT-5.5 | batch, nightly; real time after a rep edit | `prompts/qa.md` |
| Reply classify and draft | GPT-5.5 | real time | `prompts/reply.md` |
| Reason codes | GPT-5 nano | batch, nightly | `prompts/reasons.md` |
| Market brief | GPT-5.5 | weekly | `prompts/market.md` |

Every prompt file has YAML frontmatter: `model`, `temperature`, `max_output_tokens`, `output_schema` (a JSON Schema the response must validate against). The loader rejects a prompt without all four.

## The nightly batch

Runs after the hourly build at 01:00 in each rep's local timezone bucket (US Pacific, Central, Eastern; the playbook must be posted by 07:00 local).

1. Select accounts on tomorrow's board: `marts.playbook_daily` candidates plus any account with a new signal since the last run.
2. For each, `decide()` (pure function; inputs assembled from `core.*`). Persist to `core.decisions`.
3. For decisions with `action = research`: run brief (if stale) and prospect rows. Persist. Re-run `decide()`.
4. For decisions with an outbound action and a contact: assemble the draft prompt, run, persist to `core.drafts`; run QA; if `qa_grade < B`, one rewrite pass with the QA notes appended; persist the final draft with its grade.
5. Reason codes for every account whose score changed.
6. Write one `core.cost_events` row per model call.
7. Post the board to `slack/` (App Home) and DMs for P1s.

Batch mechanics: Cortex `COMPLETE` inside SQL where Navan's Snowflake region hosts OpenAI models; otherwise the runner writes a JSONL to stage, files an OpenAI Batch job, and a second task collects it. Both paths produce identical rows. See `integrations/openai.md`.

## Prompt assembly (the only PII gate)

`assemble(prompt_name, account_id, contact_id=None) -> str` is the single function that builds model input. It reads the brief, the signals (quote, source_url, event_date, evidence_tier), the account row minus identifiers, and for a contact: `first_name`, `title`, `persona`, `role_start`. It never reads `email`, `mobile`, `linkedin_url`, or `sfdc_id`. `test_assemble.py` greps every assembled prompt for `@`, seven-digit runs, and `linkedin.com/in/` and fails on any hit.

## Receipt discipline

- A draft's `receipts` array lists the `signal_id`s it used. QA verifies every quoted span is a verbatim substring of one of those signals' `quote`, and every factual claim about the company is traceable to a listed signal, the brief, or the CRM fields the prompt received.
- Tier 3 signals are never passed to `draft.md`. They may appear in the brief, marked "inferred, do not cite."
- If an account has no tier 1 or tier 2 signal, `draft.md` receives `no_signal = true` and uses the fit-and-timing template. The card says "No receipted signal; this touch runs on fit and timing."

## Acceptance

- [ ] `pytest agents/` passes (`test_decide.py`, `test_assemble.py`, `test_prompts_load.py`).
- [ ] On the fixture book, the nightly batch produces briefs for every P1 to P3 account, drafts with grades for every account with an outbound decision, and zero drafts for holdout or suppressed accounts.
- [ ] Larkspur's draft cites signal `sig_lark_001` and QA grades it B or better; a planted draft that paraphrases the quote inside quotation marks grades F with the note "quote altered."
- [ ] A rep edit in Slack re-runs QA in under 5 seconds and shows the new grade.
- [ ] `core.cost_events` has one row per model call with non-null tokens and `cost_usd`.
- [ ] Changing `model:` in a prompt's frontmatter changes the model used with no other code change.
