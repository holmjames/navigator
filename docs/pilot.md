# Pilot

Three weeks to a live pod of 10 to 20 reps. Then pods of fifty a week. Every Friday ends with a demo the pilot pod's manager can react to.

## Week by week

| Week | Done means | Friday demo |
|---|---|---|
| **1, foundation** | The book is in Snowflake with one `account_id` per account and a match rate we can argue with (`core.review_queue` is the argument). Five plays fire on real accounts. Every account has a score with three reasons. The Slack bot posts a plain card. | The board for one pod, ranked, with reasons. No drafts yet. |
| **2, agents** | Briefs cached for the pod's accounts. Drafts with QA grades. Verified email for most P1 contacts and a warm path where one exists. The morning playbook runs for the pod. Tier A stays off. | A rep's morning, live, on real accounts. |
| **3, the loop** | Taps enroll in Apollo and land on Nooks lists. Replies are classified and drafted. Centralize is on live deals for the AE handoff. Outcomes are written. The manager view is live. Tier A turns on for SMB in `AUTO_GEOS` with caps. | Signal to meeting, end to end, with the log beside it. |
| **After** | Tier boundaries tuned from the first month's replies. Each new pod gets the same three Friday demos, compressed into one. First weight refit when `core.outcomes` holds 300 attributable meetings. | |

## If procurement is slower than three weeks

Week one runs on tools already approved. Each new vendor joins the waterfall when it clears security, and nothing downstream changes shape.

| Layer | Day one | When cleared |
|---|---|---|
| Signals | Clay plays on job posts, funding, tech detection, Claygent; SteadyBase if already in place | SteadyBase for receipted quotes on the public book |
| Identity | Domain-first ladder in Snowflake with a review queue, Salesforce ids mapped | The SteadyBase resolver for LEI, CIK, and the corporate tree |
| Contacts | Apollo | MoltSets in front of Apollo |
| Warm paths | None; relationship scores zero and the orchestrator goes cold | TheSwarm on the book, then Centralize on live deals |
| Everything else | Snowflake, Salesforce, Apollo sequences, Nooks, Slack, OpenAI | Unchanged |

## The holdout

Measured from week 1 so there is a baseline, with an **account-level holdout inside the pilot pod**: the same reps, a random 30% of their accounts flagged `holdout = true` in `core.account`. Holdout accounts get no Navigator card, no agent touch, no enrichment beyond what the rep would have done; the reps work them the old way. A separate control pod would carry manager and territory differences, and reps talk.

Randomization is by `account_id` hash, stratified by segment and priority at the moment of assignment, and frozen for the pilot. The holdout flag is visible in Salesforce so nobody wonders why an account has no card.

## Metrics

| Metric | Definition | Target |
|---|---|---|
| Signals actioned within 24 hours | Share of P1 and P2 cards with a rep action (approve, edit-and-send, call, intro request) or an auto send within 24 hours of posting | 70% or better. Today's number is unknown; measuring it is the first finding. |
| Reply rate | Replies (any class except unsubscribe and bounce) per touch, Navigator accounts versus holdout, by play and tier | Above holdout |
| Meetings per rep per week | Meetings booked, Navigator accounts versus holdout, same reps | Above holdout |
| QA grade versus reply rate | Reply rate by `qa_grade` bucket. A-graded emails should out-reply B-graded ones. If not, the grader is wrong and gets fixed before the sends do. | Monotonic |
| Research minutes per day | Self-reported by the pod, week 1 and week 3 | Down |
| Cost per meeting, all in | `core.cost_events` (model tokens plus vendor rows) divided by attributable meetings | Reported, not targeted, in the pilot |

Attribution: a meeting is Navigator-attributable when the booking contact received a Navigator touch (any channel) in the 30 days before the meeting was created. The holdout makes the comparison honest even when attribution is generous.

## Roles

| Who | Does |
|---|---|
| GTM engineer | Owns the repo, the agents, the plays, the Slack app, the cost meter, the Friday demo. Writes the specs, generates the code, reviews it, ships it. |
| Data engineer (part time, heaviest in week 1) | Snowflake access and warehouses, the Salesforce connector, dbt review, compute guardrails. |
| RevOps | Salesforce fields and task types, suppression rules, territory mapping onto `account_id`, the definition of "actioned." |
| Pilot pod manager | Picks the reps, sets tier boundaries with sales leadership, brings Friday feedback, decides when Tier A turns on. |
| Security and legal | Vendor review and DPAs; `core.geo_rules`; retention for transcripts and contact data. |
| Enablement and product marketing | The voice guide and the product-claims library the QA agent checks drafts against. |
