# slack/ — the rep interface

**Owns:** the Bolt app: App Home playbook list, account cards, action handlers, the reply thread, the manager view, three slash commands.

**Reads:** `marts.playbook_daily`, `marts.manager_daily`, `marts.actioned_24h`, `core.drafts`, `core.decisions`.
**Writes:** `core.touches` (on approve or send), `core.drafts` (new version after edit), `core.audit`, `core.switches` (slash commands). Calls `agents/` for QA after an edit. Calls Apollo, Nooks, TheSwarm, Salesforce through `integrations/` clients on a tap.

This is one of the three places code is required (see `docs/decisions.md` #4): Slack needs the interaction endpoint to acknowledge within three seconds, and Edit opens a modal.

## Surfaces

| Surface | What it shows | Refresh |
|---|---|---|
| **App Home** | The rep's board: P1s, then P2s, then P3s, sorted by score. One row per account: name, score, priority, one reason line, the proposed action, a chevron to open the card. A filter chip row: today, snoozed, sent, replies. | On open, and after every action |
| **DM** | P1 cards in full, and every reply thread. Nothing else. Nine cards a day belong in App Home, not in a DM. | 07:00 local for P1s; live for replies |
| **Card** (modal or message) | See `cards.md`. Brief, score with reasons, committee, draft with grade and QA notes, next-best-action plan, buttons. | |
| **Manager view** (App Home tab for managers) | Pod metrics from `marts.manager_daily` and `marts.actioned_24h`: signals fired, actioned within 24h, reply and meeting rate by play and tier, QA grade versus reply rate, cost per meeting. Drill to rep. | On open |
| **Monday brief** | The market agent's output, posted to the pod channel. | Weekly |

## Actions

| Button | Handler | Result |
|---|---|---|
| Approve and send | Verify `qa_grade >= C` and the contact is not suppressed (second suppression check); enroll in Apollo (or send the LinkedIn note task); write `core.touches` with `draft_id`, `qa_grade`, `sent_by = rep`; Salesforce task; update card to "Sent 8:12 AM" | Card collapses to a sent state |
| Request intro | TheSwarm intro request to the connector with the brief attached; Apollo fallback enrolled on hold, first step in 3 business days; `core.touches` with `channel = warm_intro`; Salesforce task | Card shows "Intro requested from Jenna; email fallback Thu 8:10 AM" |
| Edit | Opens a modal with subject and body; on submit, saves `core.drafts` version n+1, runs QA in real time, shows the new grade and notes; the rep can then Approve | Under 5 seconds round trip |
| Call now | Adds to the rep's Nooks list at the top with the opener; Salesforce task | |
| Snooze 3 days | `core.decisions` gets a `wait` with `when = today + 3`; card hides; re-checked for new signals before it returns | |
| Disqualify | Modal asks for a reason (not a fit, competitor, wrong segment, other); Salesforce field set; account suppressed 90 days; `core.audit` | |
| Send reply (in a reply thread) | Sends through Apollo on the same thread; `core.touches`; Centralize marks engaged | |

Every handler acknowledges within 3 seconds and does the work after; failures post an ephemeral message with what to do.

## Slash commands (GTM engineer and pilot manager only)

- `/navigator pause tier A`, `/navigator resume tier A`
- `/navigator pause play <name>`, `/navigator resume play <name>`
- `/navigator pause all`, `/navigator resume all`
- `/navigator status` shows switches, last batch time, cards posted today, cost today

## Tier A behavior

For `autonomy = auto` touches, the card is informational: it shows what was sent, when, the grade, and an Undo button that is live for 10 minutes (Apollo's step delay is set to 10 minutes for Tier A sequences so an undo cancels before the send).

## Acceptance

- [ ] `manifest.yml` installs the app with only the scopes listed there.
- [ ] App Home renders the fixture pod's board in under 2 seconds with 40 accounts.
- [ ] Every button's handler acknowledges in under 3 seconds under a 50-concurrent-tap load test.
- [ ] Approve on a suppressed contact (planted after the card was built) refuses with the reason and writes `core.audit`.
- [ ] Edit, then QA, shows a new grade in under 5 seconds and stores a new draft version.
- [ ] `/navigator pause tier A` flips every Tier A card to "approve" within one minute.
- [ ] No card is ever posted for a holdout account.
