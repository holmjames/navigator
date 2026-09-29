# Centralize

Relationship intelligence for live deals: automatic org charts and buying-committee maps from CRM, email, calendar, and call recordings; who is engaged, who has gone quiet, who is missing; warm intros through the team's network; next best move; an AI strategist ("Centra"). Verified against `https://www.usecentralize.com/` and `/pricing` on 2026-09-28.

## How Navigator uses it

| Use | When |
|---|---|
| Account map created when a P1 or P2 account first gets a touch; the missing stakeholder flagged | Layer 4, after the first send |
| Contact marked engaged on reply; coverage count on the card | Reply flow |
| BDR to AE handoff: the map shared with the AE on meeting booked, with who is not yet engaged | Meeting flow |
| Next-move recommendations surfaced in Slack once a deal is live | Post-handoff |

Centralize and TheSwarm both find warm intros. TheSwarm runs in bulk before contact; Centralize runs per deal after. If budget forces one, start with TheSwarm in Clay and add Centralize for the AE handoff (`docs/decisions.md`).

## Integrations (from their site)

Salesforce, Slack, Gmail, Outlook, Google Calendar, Notion, Gong, "and more." Slack app available. Salesforce Ventures backs the deepest integrations. SOC 2 Type 2, SSO, RBAC, scoped OAuth, customer-controlled retention.

## Pricing (2026-09-28)

| Plan | Price | Includes |
|---|---|---|
| Free | $0 | 5 Standard accounts, auto org charts and maps, LinkedIn warm-connection sync, Chrome extension, email and calendar |
| Pro | $49/user/month | 50 Standard accounts, 5 Smart accounts (full intelligence: live org charts, relationship scoring, missing-stakeholder detection), Centra, suggested contacts, AI priorities and drafted outreach, 1,000 email and 100 phone enrichment credits; extra Smart accounts $5/month each |
| Enterprise | custom, annual | Salesforce integration, call recorder and sequencer integrations, SSO, MFA, dedicated Slack support |

Navigator needs Enterprise (Salesforce integration). The demo math uses $49 a seat for 100 seats (AEs and managers on live deals) as a list-price stand-in.

## To verify

- [ ] **Whether Centralize has a public API or webhooks at all.** The site lists integrations, not an API. If not, the integration is: Salesforce sync in both directions (Centralize reads opps and contacts; Navigator reads Centralize's engagement fields if they are written back), and the handoff map is a Centralize link on the opp. `docs/decisions.md` open item E.
- [ ] Whether engagement state ("engaged", "gone quiet", "missing") is written to Salesforce fields Navigator can read.
- [ ] Enterprise pricing for ~100 seats.
