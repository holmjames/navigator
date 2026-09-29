# evals/

The golden set. Runs in CI on every prompt change and every scoring change. Nothing about Navigator's quality is asserted in prose that isn't asserted here.

## What's in it

| Path | What |
|---|---|
| `fixtures/book.csv` | 200 fictional accounts (15 public), with the firmographics scoring needs. Six planted identity ambiguities. Larkspur Dynamics is `acc_larkspur`. |
| `fixtures/signals.json` | Signals for the fixture accounts with quotes, `https://` source URLs (fictional receipt hosts), event dates, and evidence tiers. |
| `fixtures/contacts.json` | Committee members per account: first name, title, persona, role_start, country. No emails, no phones. |
| `fixtures/warm_paths.json` | A few paths, including Jenna → Miguel at 0.82. |
| `fixtures/claims.json` | A placeholder product-claims library (three safe, generic statements) so QA has something to trace to. |
| `golden/briefs/*.json` | Expected brief content per account: required facts, forbidden facts, `no_signal` flag. |
| `golden/drafts/*.json` | Draft cases: inputs plus the expected grade band and the notes QA must raise. Includes planted failures: an altered quote (must be F), an unreceipted claim (D at best), a personal email in the body (F), a 160-word body (C at best). |
| `golden/replies/*.json` | Reply texts with expected class and extracted fields. |
| `golden/scores.json` | Expected score components per fixture account (Larkspur: 37/32/12/10 = 91). |

## How it runs

```
uv run pytest evals/            # scoring (SQL against DuckDB with the Snowflake dialect shim), decide(), assemble()
uv run evals/run_prompts.py     # calls the model on golden/ cases; asserts grade bands and required/forbidden strings; writes a report
```

`run_prompts.py` needs `OPENAI_API_KEY` and costs a few dollars per run; it runs on prompt PRs only. Scoring and rules tests run on every PR and cost nothing.

## Assertions the prompt evals make

- Brief: every required fact present with its `[sig_...]` marker; every forbidden fact absent; `no_signal` correct; every quote verbatim.
- Draft: word count in range; `quoted_spans` are verbatim substrings of receipts; `receipts_used` ⊆ allowed; no banned phrase; no `@` or digit runs of 7+.
- QA: planted failures get their ceiling grade; a clean draft gets B or better; the same draft graded three times gets the same grade (temperature 0).
- Reply: class matches; dates extracted; `objection` produces no draft; `unsubscribe` produces no draft.
- Reasons: 1 to 3 lines, each starting with a component name, no facts absent from inputs.

## Adding a case

Copy an existing JSON, change the inputs, state the expectation, run it locally, commit it with the prompt change it motivates.
