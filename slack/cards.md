# Cards

Block Kit layout for the account card. The Slack app renders it from one `marts.playbook_daily` row plus the committee and warm path. Every block maps to a column.

## Account card (P1 in a DM; any priority from App Home)

```
[header]      Larkspur Dynamics                                  P1  ·  91   ← name, priority, score (mono)
[context]     Tier B · mid-market · US · owner: you                 ← tier, segment, country, owner

[section]     Why now (receipted)
              "We're consolidating our travel and expense tools onto a single platform
               in the first half. That's part of the $40 million efficiency program."
              Dana Whitcombe, CFO, Q3 earnings call, Sep 28            ← quote block; verbatim
[context]     receipt: transcript 00:31:12  ↗                        ← source_url link; green dot if tier 1

[section]     Score  91                                              ← the four bars as text: fit 37/40, signal 32/35, timing 12/15, relationship 10/10
[section]     • signal: CFO named a T&E consolidation on the Q3 call, yesterday
              • fit: 5,200 employees, 14 offices in 6 countries, Concur detected
              • timing: controller 58 days into the role; call was yesterday, close is done

[section]     Who to talk to
              Dana Whitcombe, CFO                          email A
              Miguel Serrano, Controller, 58 days          email A · mobile · warm path 0.82 via Jenna
              Anika Rao, VP FP&A                           email B
              (no email addresses or numbers are rendered; the chips are states)

[section]     Brief                                                   ← collapsed; "Show brief" expands the five lines
[divider]
[section]     Draft to Miguel Serrano  ·  QA A-                       ← subject bold, body, then QA notes as small text
[section]     Next best action
              1. Ask Jenna for the intro first. A 0.82 warm path beats a cold A- email.
              2. If no reply in 3 business days, send the email above.
              3. Then a Nooks call the following Tuesday.
[actions]     [Request intro from Jenna]  [Send email now]  [Edit]  [Call now]  [Snooze 3 days]  [Disqualify]
[context]     No receipted signal? The card says: "No receipted signal in 90 days; this touch runs on fit and timing."
```

Rules:
- The quote block appears only for tier 1 signals and only verbatim. Tier 2 shows the artifact line ("Job posting: Travel Manager, Chicago, posted Sep 12 ↗").
- Never render an email address, phone number, or LinkedIn URL. Chips are states: `email A`, `mobile`, `warm path 0.82`.
- Buttons shown depend on the decision: `warm_intro` shows Request intro as primary; `email` shows Send as primary; `call` shows Call now as primary; `human_write` (Tier C) shows no send buttons, only Open brief, Request intro, Snooze.
- Tier A `auto` cards replace the actions row with `Sent 7:02 AM · A · [Undo]` for ten minutes, then `Sent`.

## Sent state

```
[section]     ✓ Intro requested from Jenna, 7:06 AM. Email fallback scheduled Thu 8:10 AM. Salesforce task logged.
```

## Reply thread (DM)

```
[header]      Reply from Miguel Serrano · Larkspur Dynamics · interested
[section]     > Happy to chat. We're looking at options through Q1 ... (the reply, quoted)
[section]     Draft reply  ·  QA A
              Miguel, thanks, and thank you Jenna. Multi-entity EU is the normal shape for us ...
[actions]     [Send reply]  [Edit]  [Hand to AE]
[context]     Sequence stopped. Centralize: controller marked engaged, coverage 1 of 3.
```

For `objection` and unknown classes, the actions row is `[Open in Apollo] [Hand to AE]` and the summary line replaces the draft.

## App Home row

```
Larkspur Dynamics        91  P1   signal: CFO named a T&E consolidation ...        Request intro   ›
Ostrander Medical        71  P2   timing: new VP Finance, 41 days                Email           ›
```

## Manager view (App Home, managers)

Four stat tiles (signals fired, actioned in 24h %, reply rate, meetings), then a table by play × tier with touches, replies, meetings, and a small QA grade vs reply rate table. Numbers come from `marts.*`; no computation in the app.
