# Apollo

Two roles: the email sequencing engine (sends, caps, unsubscribes, replies, bounces) and the contact fallback behind MoltSets in the waterfall. Already on Meridian Travel's stack; pricing not modeled.

## Sequencing

| Need | How |
|---|---|
| Enroll a contact in a sequence with Navigator's draft as step 1 | Apollo API: create or reuse a per-play sequence with a single templated step whose body is the approved draft; enroll the contact; record `sequence_id` on `core.touches` |
| Hold and release (warm-intro fallback) | Enroll with the first step delayed 3 business days; cancel on intro reply |
| Tier A undo window | Tier A sequences have a 10-minute first-step delay; the Slack Undo cancels the enrollment |
| Caps | Sequence and mailbox daily limits set to 40 per rep; Navigator's `decide()` cap is the same number; the lower wins |
| Unsubscribe and bounce handling | Apollo's own; events flow to `raw.apollo_events` and suppress the contact in `core.contact` |
| Replies | Apollo reply webhook → n8n `apollo-events` → reply flow. Navigator never reads rep inboxes directly (`docs/decisions.md` #11) |

Events consumed: `email_sent`, `email_opened`, `email_replied`, `email_bounced`, `contact_unsubscribed`, `sequence_finished`.

## Contact data

Second in the waterfall: called from the Clay column when MoltSets returns `not_found` or a grade below B. Apollo's email confidence maps to grades: verified → A, likely → B, guessed → not used.

## To verify

- [ ] Reply webhook availability on Meridian Travel's Apollo plan and its payload (message id, thread, reply text).
- [ ] Whether per-sequence first-step delays can be set by API.
- [ ] Deliverability setup: sending domains, warmup, and whether Tier A volume needs additional mailboxes.
