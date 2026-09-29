# Rules of engagement

What the orchestrator does with an account, in order. The code is `agents/orchestrator/decide.py`; the tests in `agents/orchestrator/test_decide.py` are the authoritative reading of this document. If a rule here cannot be expressed as a test, it is not a rule yet.

The orchestrator wakes for an account when its score changes, a new signal lands, a reply arrives, or a scheduled follow-up comes due. It returns one decision:

```
Decision(
  action:    suppress | route_to_ae | expansion_handoff | review | wait | research
           | warm_intro | email | call | linkedin | meeting_flow | human_write
  autonomy:  auto | approve | research_only
  when:      now | <date>
  contact_id: the person the touch goes to, if any
  reason:    one sentence, shown on the card and written to core.touches
)
```

## Gates, in order

1. **Suppression.** If the account or the contact is in `core.v_suppressed` (do-not-contact, unsubscribed, competitor, legal hold, active customer where expansion is out of scope) → `suppress`. No card.
2. **Customer.** If `is_customer` → `expansion_handoff`: write a Salesforce note to the CSM with the signal; no BDR touch. Expansion plays are a later phase.
3. **Open opportunity.** If `has_open_opp` → `route_to_ae`: post the signal and the brief to the AE's channel. The BDR does not touch the account. This is the most common way a good signal reaches the wrong person; do not suppress it, route it.
4. **Named account, no opp.** If `owner_type = 'ae'` and no open opp → the card goes to the AE's BDR partner with `autonomy = research_only` unless the AE has opted the account into Navigator touches (`ae_opt_in`).
5. **Priority.** If `priority = 'P4'` → `wait`. No card unless the score moved 10 or more since the last decision.
6. **Quiet period.** If the account is public, the next earnings call is within 14 days, and the target persona is in finance → `wait` until 2 business days after the call. Reaching a controller in the close is the wrong moment; the week after the call is the right one.
7. **Review queue.** If the account's identity is `ambiguous` or `conflict` → `review`. Nothing is sent to a company we are not sure of.
8. **Caps.** If the rep has reached `SENDS_PER_REP_PER_DAY` (40) → `wait` until tomorrow. If the contact has had `TOUCHES_PER_CONTACT_PER_WEEK` (2) in the last 7 days → `wait` 7 days from the last touch. If the account has had 3 touches with no reply → `wait` 30 days.
9. **Freshness.** If the brief is missing or `fresh_until < today` → `research`. The agents run, then `decide()` runs again.

## Channel choice

Once every gate passes, pick the channel for the best contact on the committee (persona rank, then verified channel):

| Condition | Action | Fallback |
|---|---|---|
| A warm path with strength ≥ 0.70 to any committee member | `warm_intro` through the connector, with the brief attached | If no reply from the connector in 3 business days, `email` |
| Verified email grade A or B | `email` | |
| No usable email but a verified mobile, and calls are permitted in the contact's country | `call` (Nooks list, with the opener) | |
| Neither | `linkedin` (note under 300 characters) | |
| Committee has no contact with a verified channel | `research` (prospect research runs) | |

## Autonomy

Set from tier and geography, never from the score:

| Tier | Autonomy | Meaning |
|---|---|---|
| A and `country in AUTO_GEOS` and `qa_grade >= B` | `auto` | The touch sends on its own within caps. The card is informational. |
| A outside `AUTO_GEOS`, or any B | `approve` | The card has the draft and a button. Nothing sends without a tap. |
| C | `research_only` | Brief, committee, warm path, proposed timing. A human writes every word. `human_write` is the action. |

`AUTO_GEOS = {US, CA}` at launch. EU and UK contacts are never `auto` (see `docs/tiers.md`).

## After a touch

| Event | Next decision |
|---|---|
| Email sent, no reply in 4 business days | `call` if a verified mobile exists and calls are permitted, else a second `email` (different angle, same receipt) |
| Second touch, no reply in 5 business days | `linkedin` |
| Third touch, no reply | `wait` 30 days, then re-evaluate on the next signal |
| Reply classified `interested` | `meeting_flow`: reply agent drafts with two times; sequence stopped; Centralize marks the contact engaged |
| Reply classified `question` | `meeting_flow` with the answer drafted from the enablement library only; unknown answers go to a human |
| Reply classified `objection` | `human_write`: the reply agent classifies and summarizes; a person answers |
| Reply classified `not_now` with a date | `wait` until that date, then `email` |
| Reply classified `not_now` without a date | `wait` 90 days |
| Reply classified `out_of_office` | resend the same touch 1 business day after the return date, or in 7 days if no date |
| Reply classified `referral` | new contact created from the referral, `email` to them referencing the referrer, original contact marked `referred` |
| Reply classified `wrong_person` | contact demoted, prospect research reruns for the account |
| Reply classified `unsubscribe` | contact suppressed permanently; account untouched |
| Meeting booked | Salesforce event and opp at Discovery; AE assigned; Centralize handoff map; Nooks call prep; account leaves the BDR board |
| Bounce | contact's email marked invalid, suppressed for 90 days, re-verified through the waterfall before any retry |

## Routing the card

The card goes to the account owner in Salesforce when `owner_type = 'bdr'`. Unowned accounts in a territory go to the territory's round-robin (a Salesforce assignment rule Navigator calls, never one it re-implements). Managers see everything in their pod in the manager view.

## Things the orchestrator never does

- Send anything to a contact without a verified channel and a `qa_grade`.
- Merge or re-point an `account_id`.
- Change a Salesforce owner.
- Write to Salesforce without the `draft_id` and `touch_id` on the task.
- Call a model. It is a decision function; the agents call models.
