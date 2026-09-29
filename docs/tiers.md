# Autonomy by tier

How 500 reps become 1,000 without the ops team doubling: the agent's freedom scales with how little a mistake costs.

| Tier | Who | Agent may | Guardrails |
|---|---|---|---|
| **A** | SMB: `segment = 'smb'` (Salesforce field; roughly under 200 employees) and `country in AUTO_GEOS` | Send email and LinkedIn touches on its own | `AUTO_GEOS = {US, CA}` to start. Caps of 40 sends a day per rep and 2 touches per contact a week. QA grade B or better. Receipted claims only. Kill switch per tier and per play. |
| **B** | Mid-market: `segment = 'mid_market'`, and any Tier-A account outside `AUTO_GEOS` | Draft everything, pick the next action, enroll after a one-tap approval | The rep approves each send. Call scripts are suggestions. |
| **C** | Enterprise and strategic: `segment = 'enterprise'` or `strategic_flag` | Research, map the committee, find warm paths, propose timing | A human writes every word. Intros go through the connector, never around them. |

Tier is set from Salesforce fields (`segment`, `strategic_flag`) and the contact's `country`, never from the score. Priority (P1 to P4) is from the score and decides what is on the board; tier decides what the agents may do about it.

## Geography

Every contact carries a `country`. The rules:

- **`AUTO_GEOS` (US, CA at launch):** Tier A may `auto`. Cold B2B email is lawful under CAN-SPAM and CASL's implied-consent provisions when the message is about the recipient's business role, identifies the sender, and honors unsubscribes; Apollo enforces the unsubscribe.
- **EU and UK:** never `auto`. Every touch is human-approved. The basis is documented legitimate interest (a B2B role, a business email, a relevant offer), with the usual per-country differences: Germany and Austria in particular treat unsolicited B2B email restrictively, and the default for `country in {DE, AT}` is `linkedin` or `call` first, email only after a reply or an intro. Legal owns the country list; `decide()` reads it from `core.geo_rules`, not from code.
- **Everywhere:** business email only. The MoltSets personal-email endpoint is never called. Mobiles are scrubbed against the national do-not-call list where one exists before they reach a Nooks list. No SMS, ever.

`core.geo_rules` columns: `country`, `auto_allowed`, `email_first_allowed`, `calls_allowed`, `notes`, `reviewed_by`, `reviewed_at`. Empty means "not reviewed," which `decide()` treats as `approve` with `email_first_allowed = false`.

## Caps

| Cap | Value | Enforced in |
|---|---|---|
| Sends per rep per day | 40 | `decide()` and Apollo sequence settings; the lower wins |
| Touches per contact per week | 2 | `decide()` |
| Touches per account with no reply before a 30-day wait | 3 | `decide()` |
| Tier-A auto sends per play per day (all reps) | 1,500 | `ops` kill switch threshold |
| New contacts bought per day (MoltSets and Apollo) | 5,000 | `ops` row budget |

## Kill switches

`ops` exposes three, each a Slack slash command for the GTM engineer and the pilot manager and a row in `core.switches`:

- `/navigator pause tier A` stops all `auto` sends; Tier A becomes `approve`.
- `/navigator pause play <name>` stops a play from creating signals; existing cards stay.
- `/navigator pause all` stops the nightly batch and every send; cards already posted stay visible with the buttons disabled.

Resuming requires the same command with `resume` and is logged to `core.audit`.
