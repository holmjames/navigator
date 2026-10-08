# n8n

The flow tool for event-driven and scheduled glue. Self-hosted in Meridian Travel's cloud or on n8n's cloud plan. Chosen over Zapier because per-task pricing at Navigator's volume exceeds the model bill and Zapier cannot host the Slack endpoint (`docs/decisions.md` #5).

## Workflows

Exports live in `ingest/n8n/` with credential ids stripped. See `ingest/SPEC.md` for the table.

| Workflow | Trigger | Notes |
|---|---|---|
| `steadybase-delta` | hourly | cursor in `core.cursors`; loop once on `truncated` |
| `clay-signal-webhook` | webhook | idempotent insert |
| `apollo-events` | webhook | fans out to `reply-flow` on replies |
| `reply-flow` | called | model call through the agents service's HTTP endpoint (so prompts stay in the repo), then Slack |
| `swarm-weekly` | weekly | paged by worked account |
| `openai-batch` | nightly | only when Cortex is unavailable in region |

## Rules

- Credentials by name from n8n's credential store; never in node parameters.
- Every workflow writes one `core.cost_events` row per vendor call it makes.
- Every workflow has an error workflow that posts to `#navigator-ops` with the execution id.
- Workflows do not contain prompt text. Model calls go through the agents service so prompts, schemas, and the PII gate live in one place.

## Hosting

n8n needs a running process either way. On n8n cloud there is nothing to operate; self-hosted needs a container and someone watching it, which is one reason batch work sits in Snowflake wherever it can.

## To verify

- [ ] Whether Meridian Travel already runs n8n, Workato, Tray, or similar; use what exists.
- [ ] Network path from n8n to Snowflake (private link or IP allowlist).
