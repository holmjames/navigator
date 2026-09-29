# Play 5: stack detection

**Fires when** tech detection finds a displacement target (Concur, Expensify, TravelPerk, Egencia, Emburse, Zoho Expense, Ramp Travel, another managed-travel platform) or a corporate card program (Amex, Brex, Ramp, Divvy).

This play does not write a `core.signals` row on its own. It sets `core.account.stack_detected` (`displacement`, `card_only`, `none`), which feeds the fit term (10, 5, or 3 points), and it adds a line to the brief. Combined with any other play on the same account, it changes the draft's angle (displacement versus first-time managed travel).

## Both public and private (Clay)

Table `play-05-stack`:

| Column | Provider | Notes |
|---|---|---|
| Domain | from Snowflake (all non-suppressed accounts) | input |
| Tech stack | Clay tech-detection providers (BuiltWith, Wappalyzer, or the job-posting technology mention provider) | |
| Displacement target | formula over the stack list against the target list | |
| Card program | formula | |
| Evidence URL | the job posting or page where the tool is named, when the provider returns one | tier 2 when present; otherwise the detection is a fit input only and is not cited |

Budget: 12,000 rows/month (every account once per 14 days at most; in practice once a quarter unless another play touches the account).

## What the card says

"Stack: Concur (job postings ↗), Amex corporate card." When there is no evidence URL: "Stack: Concur detected (not citable)." The draft never names the competitor unless the evidence is tier 2 and first-party.
