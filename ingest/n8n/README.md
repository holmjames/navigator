# n8n workflow exports

One JSON export per workflow, credential ids stripped. The table of workflows and their steps is in `../SPEC.md`; hosting notes are in `../../integrations/n8n.md`.

Not yet exported (the workflows are specified, not built):

- `steadybase-delta.json`
- `clay-signal-webhook.json`
- `apollo-events.json`
- `reply-flow.json`
- `swarm-weekly.json`
- `openai-batch.json`

Export with credentials removed: `n8n export:workflow --id <id> --pretty | jq 'del(.. | .credentials?)' > <name>.json`.
