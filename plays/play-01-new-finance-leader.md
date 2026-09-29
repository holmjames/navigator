# Play 1: new finance leader

**Fires when** a CFO, controller, chief accounting officer, VP finance, or head of procurement at an account on the book has been in role between 30 and 120 days. New leaders own vendor consolidation, and the first 120 days is when they do it.

**Writes** `signal_type = leadership_change`, base 22.

## Public accounts (SteadyBase)

- Nightly: `pg_people(persona in {cfo, controller, chief_accounting_officer, vp_finance, procurement}, new_in_role_days=120)` on the book. Identity only; the row carries `linkedin_url`, `role_start`, `source`, `source_ref`.
- Also: `search(query="appointed chief financial officer", kinds=["documents"], since_days=120)` for 8-K item 5.02 filings, which are tier 1 (the filing is the receipt).
- Evidence tier: 1 when an 8-K or IR page names the appointment; 2 when the source is a vendor roster row with a LinkedIn URL.
- The contact is created in `core.contact` with `persona` and `role_start`; MoltSets verifies the email in the waterfall.

## Private accounts (Clay)

Table `play-01-new-finance-leader`:

| Column | Provider | Notes |
|---|---|---|
| Domain | from Snowflake (accounts where `is_public = false` and not suppressed) | input |
| Find people | Clay people search: titles `CFO, Chief Financial Officer, Controller, VP Finance, Head of Procurement`, current company = domain | 1 credit per row |
| Job change | Clay job-change / "recently changed jobs" enrichment on each person | flags a role start in the last 120 days |
| Role start | from the job-change result | |
| LinkedIn URL | from people search | identity key |
| Artifact URL | the LinkedIn profile URL is **not** an artifact for outreach; if a press release or company news page announces the hire, Claygent finds it (`"appointed" OR "joins as" + name + company`) and that URL is the artifact | tier 2 if found, else tier 3 |
| Suppression | `exclude_company_domain` = `core.v_suppressed` domains | applied at search time |

Budget: 4,000 rows/month. Re-run per account every 14 days.

## What the card says

Tier 1 or 2: "New controller: Miguel Serrano, 58 days in role [8-K, Aug 2 ↗]". Tier 3: the brief lists it under inferred; the draft does not mention it; the timing term still scores it (`role_start` is a fact even when the announcement is not quotable).

## SteadyBase trigger (optional, for the transcript lane)

```
define_trigger(name="Navigator: new CFO or controller",
               criteria_text="any account in my book files an 8-K naming a new CFO, controller, or chief accounting officer",
               scope="documents", filters={"lookback_days": 120})
```
