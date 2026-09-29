# Nooks

The dialer. Call lists from the orchestrator, call prep from the brief, transcripts and dispositions back to Snowflake. **Not verified**: this file records what Navigator needs from Nooks, not what Nooks has been confirmed to offer.

## What Navigator needs

| Need | Preferred | Fallback |
|---|---|---|
| Push a call list per rep (contact, priority, the opener text, the brief link) | API or webhook-driven list creation | Nightly CSV import of the rep's list, generated from `marts.playbook_daily` where `action = call` |
| Pull dispositions and call outcomes | Webhook per call → n8n → `raw.nooks_calls` | Nightly export, or read the Salesforce activity Nooks writes |
| Pull transcripts (or the recording URL) | Webhook with transcript text | Read from the call recorder Nooks syncs to (Gong or equivalent) |
| Show call prep in the dialer | A notes or "talk track" field populated per contact | The Slack card open beside the dialer |

Mobiles reach a Nooks list only when `core.geo_rules.calls_allowed` is true for the contact's country and the number has been scrubbed against the applicable do-not-call list (`docs/tiers.md`). No SMS.

## What flows back

`raw.nooks_calls` → `core.outcomes` (`kind = call`, `detail` with disposition and duration) → the account brief's next refresh includes what the contact said, and objections feed the reply agent's summary for the rep.

## To verify

- [ ] **Whether Nooks exposes a public API** for list creation and call events, and its auth model. `docs/decisions.md` open item D.
- [ ] Whether Nooks writes call activities to Salesforce with a field Navigator can key on (`navigator_touch_id__c`).
- [ ] Transcript retention and where transcripts live today.
