# Live scenarios (MCP Failure Lab)

Read-only scenarios for [MCP Failure Lab](https://github.com/anilloutombam/mcp-failure-lab).
Each one makes a real call through a real MCP SDK client against the live server,
then a second call in the same session: the point is whether the session survives
a failed call, and whether a tool's refusal reaches the model as a readable
`isError` result instead of a JSON-RPC error the client throws on.

```bash
export WORKLORE_MCP_AUTHORIZATION="Bearer $WORKLORE_TOKEN"
for s in tests/live_scenarios/*-*.json; do
  npx -y mcp-failure-lab@0.11.0 run "$s" --target tests/live_scenarios/target.json
done
```

Since 0.5.0 searching and reading public stories needs no token. The `anon-*`
scenarios prove that with `target-anon.json`, which sends no `Authorization`
header at all:

```bash
for s in tests/live_scenarios/anon-*.json; do
  npx -y mcp-failure-lab@0.11.0 run "$s" --target tests/live_scenarios/target-anon.json
done
```

Never add a scenario that publishes, edits or reports: these run against production.
