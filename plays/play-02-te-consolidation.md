# Play 2: T&E consolidation

**Fires when** a company says, in its own words, that it is consolidating, switching, reviewing, or renegotiating its travel and expense tools, or names travel or T&E inside a cost program.

**Writes** `signal_type = vendor_change` (base 30) or `cost_program` (base 26).

## Public accounts (SteadyBase)

Two triggers on the tenant, delivered to Slack, webhook, and the `whats_new` delta feed:

```
define_trigger(name="Navigator: T&E tool consolidation",
               criteria_text="a company on my book says it is consolidating, replacing, or reviewing its expense or travel tools",
               scope="all", filters={"lookback_days": 120})

define_trigger(name="Navigator: cost program names travel",
               criteria_text="a company on my book describes a cost reduction or efficiency program that mentions travel, T&E, or discretionary spend",
               scope="transcripts", filters={"lookback_days": 120})
```

Every hit arrives with the verbatim `quote`, `receipt_url`, `char_start`, `char_end`, and a judge verdict. Tier 1. The ingest layer keeps the quote exactly and stores the receipt URL as `source_url`.

Also read: `pg_account_signals(signal_type="vendor_change")` and `pg_account_signals(signal_type="cost", q="travel")` across the book, nightly, for signals the triggers predate.

## Private accounts (Clay)

Table `play-02-te-consolidation`:

| Column | Provider | Notes |
|---|---|---|
| Domain | from Snowflake (private, not suppressed) | input |
| Newsroom URL | Claygent: find the company's press or news page | 1 run per account per 14 days |
| Consolidation mention | Claygent: "Does the company's newsroom, blog, or a public executive post in the last 90 days mention consolidating, switching, or reviewing travel, expense, or T&E tools, or a cost or efficiency program that names travel? Return the exact sentence and the URL, or NONE." | the answer must include a URL to count |
| Artifact URL | from the Claygent answer | tier 2 when a URL is returned with an exact sentence; NONE rows write nothing |
| Quote | the exact sentence | stored verbatim; QA allows quoting a tier 2 artifact sentence only when the URL is a first-party page (press release, blog, IR page) |

Budget: 3,000 Claygent runs/month. This is the most expensive play per row and the highest-value; it runs only on accounts with `fit >= 25`.

## What the card says

Tier 1: the quote block with speaker, event, date, receipt link. Tier 2: "Press release, Sep 12 ↗: 'we are consolidating our expense tools ...'".
