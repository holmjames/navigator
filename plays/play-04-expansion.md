# Play 4: expansion

**Fires when** an account announces a new office, a new country, a headcount plan, or a funding round.

**Writes** `signal_type = expansion` (base 18) or `funding` (base 16). M&A from filings writes `m_and_a` (base 16) on public accounts.

## Public accounts (SteadyBase)

- `search_company_signals(query="office expansion new office", lane="expansion")` and `search_transcripts_local(query="EMEA APAC expansion international offices", since_days=90)` nightly, filtered to the book.
- `pg_deals()` for announced and pending M&A, with the filing as receipt. An acquisition is when T&E programs get consolidated onto one vendor.
- Tier 1 for transcript quotes and filings; tier 2 for IR press releases.

## Private accounts (Clay)

Table `play-04-expansion`:

| Column | Provider | Notes |
|---|---|---|
| Domain | from Snowflake | input |
| Funding | Clay funding provider (Crunchbase or equivalent): last round date, amount, stage | tier 2 with the announcement URL |
| News | Clay news provider: "opens office", "new headquarters", "expands to", "hiring N" in the last 90 days | tier 2 with the article URL when first-party or major outlet; tier 3 otherwise |
| Locations | Claygent on the careers page: distinct office locations | feeds `office_countries` and `office_count` for fit |
| Artifact URL | from the provider | |

Budget: 5,000 rows/month.

## What the card says

"Series C, $80M, Sep 3 ↗" or "New Dublin office announced Aug 20 ↗". A funding round alone rarely makes P1; combined with a finance leader change it often does.
