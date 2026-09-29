# Play 3: travel and finance hiring

**Fires when** an account posts a travel manager, T&E lead, global mobility, or corporate travel role (`travel_role_hiring`, base 20), or has three or more open finance, accounting, or AP roles (`finance_hiring`, base 14).

Job postings are artifacts with URLs: tier 2, citable as "a posting for a Travel Manager in Chicago, Sep 12."

## Public accounts (SteadyBase)

- `search_company_signals(query="travel manager", lane="web_hiring_posting")` and `search_company_signals(query="finance accounting", lane="web_hiring_posting")`, nightly, filtered to the book by `account_id`.
- Rows carry the posting URL (ATS page), title, location.

## Private accounts (Clay)

Table `play-03-hiring`:

| Column | Provider | Notes |
|---|---|---|
| Domain | from Snowflake | input |
| Job postings | Clay job-postings provider (or the ATS crawl integration) with title filters: `Travel Manager, Corporate Travel, T&E, Travel & Expense, Global Mobility, Accounts Payable, Controller, Accounting Manager, FP&A, Finance Manager` | credits per lookup |
| Count by family | formula: travel roles, finance roles | |
| Artifact URL | the posting URL for the travel role; for finance hiring, the careers page URL plus the count | tier 2 |
| Location | from the posting; feeds `office_countries` when it is a new country for the account | |

Budget: 6,000 lookups/month. Re-run per account every 14 days.

## What the card says

"Hiring: Travel Manager, Chicago, posted Sep 12 ↗" or "Nine open finance roles ↗ (careers page, Sep 27)". The draft may reference the posting as a fact; it may not speculate on why it exists.
