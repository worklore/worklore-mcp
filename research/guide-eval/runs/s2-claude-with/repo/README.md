# notes-mcp

A tiny MCP server (JSON-RPC 2.0) exposing two tools over a notes store.

- `server.py` — `handle(request_json: str) -> str`, the single entry point. The HTTP
  layer (not included) passes the raw request body in and writes the returned string out.
  For a JSON-RPC notification (no `id`, e.g. `notifications/initialized`) it returns
  `None`: the HTTP layer must reply `202 Accepted` with no body.
- `tools.py` — tool implementations.
- `db.py` — storage. In production the store is backed by DynamoDB (`DynamoStore`);
  tests use `FakeStore`, which returns every number as `Decimal` exactly like DynamoDB.
  `get_store()` picks DynamoStore when `PRODUCTION_DB=1`.
- `tests/test_conformance.py` — drives `handle()` like a real client (initialize →
  initialized → `tools/list` without credentials → `tools/call` for every tool) and
  validates results against the *published* `outputSchema`. Add happy-path arguments
  to `HAPPY_ARGS` for every new tool.

Run tests: `python3 -m unittest discover -s tests`
