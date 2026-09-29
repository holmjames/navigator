# TheSwarm

Relationship data: warm intro paths across Navan employees, customers, investors, advisors, and their networks, at list scale. Verified against `https://www.theswarm.com/` and `/pricing` on 2026-09-28.

## What it provides

- Intro paths from a company domain or a person to anyone in the combined network, with a normalized `connection_strength` and the overlap type (`work`, `school`, `investor`, LinkedIn or email connection with opt-in).
- Passive mapping: work and education overlaps for Navan's people from their work history, before anyone opts in. LinkedIn and email connections require each employee to install the extension and opt in; coverage grows with that program.
- Data: 500M profiles, daily job changes, 50M companies with fundraising data.
- Surfaces: SaaS app, Chrome extension, Clay integration, Data API, HubSpot and CRM integrations, MCP ("Available on Claude").

## How Navigator uses it

| Use | Where |
|---|---|
| Warm path per committee member, weekly for worked accounts | `raw.swarm_paths` via API (n8n `swarm-weekly`) and as a Clay column in Plays 1 and 2 |
| Intro request | Slack "Request intro" → TheSwarm intro request to the connector with the brief attached; a templated note the connector edits |
| Relationship term in the score | `core.warm_paths.strength` → `docs/scoring.md` |

## Pricing (2026-09-28)

| Plan | Price | Includes |
|---|---|---|
| Free | $0 | 10 connectors, combined network, no API |
| Premium | $99/company/month ($2,990/year) | 50 connectors, full database, full API, CSV export to 10k people, 12,000 API credits/month, $0.10 per extra credit |
| Enterprise | custom | custom credits and connectors, multi-team, white-labeled extension, CSM |

Credits: 1 per people or company export; 1 per social post or reaction; 3 per live profile enrichment (Enterprise). Navigator's demo math: $99 plus $0.10 per worked account past 12,000 a month; at 500 reps that is about $1,500 a month, and Enterprise is the realistic plan for 500 connectors.

## Risk and honesty

At launch most accounts will have no path because opt-in is a program, not a setting. The relationship term scores zero for them; `decide()` goes cold. Say so in the pilot plan.

## To verify

- [ ] API endpoints and auth (the developer docs are behind the login).
- [ ] Whether intro requests can be created by API or only in the app.
- [ ] Connector limits on Enterprise for 500 reps plus customers and investors.
