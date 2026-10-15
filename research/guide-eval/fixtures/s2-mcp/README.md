# notes-mcp

A tiny MCP server (JSON-RPC 2.0) exposing two tools over a notes store.

- `server.py` — `handle(request_json: str) -> str`, the single entry point. The HTTP
  layer (not included) passes the raw request body in and writes the returned string out.
- `tools.py` — tool implementations.
- `db.py` — storage. In production the store is backed by DynamoDB (`DynamoStore`);
  tests use `FakeStore`. `get_store()` picks DynamoStore when `PRODUCTION_DB=1`.

Run tests: `python3 -m unittest discover -s tests`
