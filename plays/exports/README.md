# Clay table exports

One JSON export per play table, for review and reproduction by hand. Clay tables are built in the UI; the export is the record of what was built, not a file Clay imports. See `../SPEC.md` and `integrations/clay.md`.

Expected files once the plays are built:

- `play-01-new-finance-leader.json`
- `play-02-te-consolidation.json`
- `play-03-hiring.json`
- `play-04-expansion.json`
- `play-05-stack.json`

Strip any API key from HTTP columns before committing; keys belong in Clay's secret store.
