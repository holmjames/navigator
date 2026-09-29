# plays/ — the five signal plays

A play is a rule that turns something observable about a company into a `core.signals` row with a type, an evidence tier, a quote or artifact, and a source URL. Public accounts get most plays from SteadyBase (receipted quotes, tier 1); private accounts get them from Clay (artifacts, tier 2; research summaries, tier 3, never cited).

Each play has one file here with: what fires it, the sources for public and private accounts, the Clay table definition (columns, providers, filters), the credit budget, the `signal_type` and `evidence_tier` it writes, and what the card says.

**Owns:** the Clay tables (built in the UI, exported as JSON into `plays/exports/` for review), the SteadyBase trigger definitions, and the row budgets.

**Writes:** `raw.clay_rows` (via Clay's Snowflake destination) and `raw.steadybase_signals` (via the delta feed).

| # | Play | Fires on | Public source | Private source | Base points |
|---|---|---|---|---|---|
| 1 | [New finance leader](play-01-new-finance-leader.md) | CFO, controller, VP finance, head of procurement new in role 30 to 120 days | SteadyBase `pg_people(persona, new_in_role_days=120)`, 8-K item 5.02 | Clay job-change detection on the committee; LinkedIn headline change | 22 |
| 2 | [T&E consolidation](play-02-te-consolidation.md) | A company says it is consolidating, switching, or reviewing travel and expense tools | SteadyBase trigger "a company on my book says it is consolidating its expense or travel tools onto one vendor" | Claygent search of newsroom, press releases, and public posts for the same phrases | 30 |
| 3 | [Travel and finance hiring](play-03-hiring.md) | A travel manager, T&E lead, or three or more finance/AP roles posted | SteadyBase `web_hiring_posting` lane | Clay job postings provider, filtered by title | 20 / 14 |
| 4 | [Expansion](play-04-expansion.md) | New office, new country, headcount plan, or a funding round | SteadyBase `expansion` lane, transcripts | Clay news and funding providers, Claygent on the careers page for new locations | 18 / 16 |
| 5 | [Stack detection](play-05-stack.md) | Concur, Expensify, TravelPerk, Egencia, Emburse, or a card program detected | Clay tech-detection providers for both | Same | feeds `fit`, not `signal`; combined with any other play it raises the account's timing note |

## Budgets

Each play has a monthly row budget in `ops/` and an alert at 80%. Rows are researched once per account per 14 days (the cache); a play re-runs on an account only when its source changed. Search-time suppression (`core.v_suppressed` as `exclude_company_domain`) is applied inside the Clay table so suppressed accounts never consume a row.

## Acceptance

- [ ] Each play's Clay table export is in `plays/exports/` and matches its file's column list.
- [ ] Running each play on the fixture book produces the expected `raw.clay_rows` (`evals/fixtures/expected_plays.json`).
- [ ] No row for a suppressed or holdout account.
- [ ] Every row has an `https://` artifact URL or is tagged tier 3.
- [ ] The five SteadyBase trigger definitions exist on the tenant and `list_triggers` returns them active.
