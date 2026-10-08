# OpenAI

Models for the agent team. Meridian Travel's preference; prompts are portable (`docs/decisions.md` #1).

## Models and jobs

| Job | Model | Why |
|---|---|---|
| Brief, draft, QA, reply, market brief | `gpt-5.5` | Writing quality and the claim-to-receipt check |
| Reason codes, prospect rows, orchestrator summaries, reply classification pre-pass | `gpt-5-nano` | Classification at near-zero cost |

Prompt frontmatter names the model; a change is a one-line PR. `gpt-5.6-sol` is a candidate for the drafting jobs at its promotional price (through 2026-11-21); evaluate on the golden set before switching.

## Modes

| Mode | Used for | Discount |
|---|---|---|
| Batch API | Every nightly job (briefs, drafts, QA, reasons, prospect rows) | 50% on input and output |
| Prompt caching | The shared prefix of every prompt (system text, voice guide, claims library) | Cached input at 10% of the standard rate |
| Real time | Replies, QA after a rep edit | none |

Batch mechanics when Cortex is not available: the runner writes one JSONL per job to a Snowflake stage, uploads to `files`, creates a batch with the `responses` endpoint, and a second task polls and writes results to `RAW` then `CORE`. Failures in a batch are retried once real time for P1 accounts only; everything else waits for the next night.

## Structured output

Every prompt has a JSON Schema (`agents/prompts/schemas/`). Calls use structured outputs with the schema; a response that fails validation is retried once with the validation error appended, then written to `raw.ingest_rejects` with `source = openai`.

## Pricing (2026-09-28, list)

| Model | Input per 1M | Output per 1M | Cached input |
|---|---|---|---|
| gpt-5.5 | $5.00 | $30.00 | 10% |
| gpt-5.6 Sol (promo) | $4.00 | $20.00 | 10% |
| gpt-5-nano | $0.05 | $0.40 | 10% |

`ops/prices.yml` is the source of truth for the cost meter.

## Cost at 500 reps (demo defaults)

About $2,900 a month with batch and caching; 13% of the run bill. Rows and seats are the bill, not tokens.

## To verify

- [ ] Meridian Travel's OpenAI organization, data-retention settings (zero data retention for API calls if required by security), and whether the enterprise agreement covers the Batch API.
- [ ] Rate limits for the nightly window (105,000 drafts a month is about 5,000 a night).
