# core models

One model per `CORE` table in `data/schema.sql`. `signals.sql` is written as the pattern; the rest follow it:

| Model | Sources | Notes |
|---|---|---|
| `account_ids.sql` | `sfdc_account`, `steadybase_*`, `clay_rows`, the resolver outputs | The id map. `(id_type, id_value)` unique. |
| `account.sql` | `sfdc_account` joined to `account_ids`, `steadybase_events` for the calendar, `clay_rows` play-05 for stack, headcount providers for growth | Tier derived from `segment_c`, `strategic_flag_c`, and country per `docs/tiers.md`. `holdout` from `navigator_holdout_c`. |
| `contact.sql` | `sfdc_contact`, `steadybase_people`, `moltsets_contacts`, `clay_rows` play-01 | Keyed `(account_id, linkedin_url)`. Persona from `agents/prompts/prospect.md` output or the SteadyBase persona key. |
| `signals.sql` | written | |
| `warm_paths.sql` | `swarm_paths` joined to contacts by LinkedIn URL | |
| `briefs.sql`, `drafts.sql`, `decisions.sql`, `touches.sql`, `outcomes.sql` | written by the agents runner and the Slack app, not by dbt; dbt only tests them | |
| `review_queue.sql` | resolver outputs | |

Tests in `../schema.yml` (to write): `not_null` and `unique` on every primary key; `accepted_values` on `signal_type`, `evidence_tier`, `priority`, `tier`, `autonomy`; the three custom tests in `../../tests/`.
