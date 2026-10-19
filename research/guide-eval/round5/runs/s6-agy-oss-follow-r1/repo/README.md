# notes-mcp

A small remote MCP server for my garden notes, meant for Claude Code, Codex
and Gemini clients. Streamable HTTP, JSON responses, Python standard library.

```
python3 server.py              # http://127.0.0.1:62559/mcp
PORT=9000 python3 server.py
```

Tools: `search_notes` (read), `get_note` (read), `add_note` (write, needs
`Authorization: Bearer dev-token-123` in development).

Not yet listed in any registry. No CI. Logs go to stderr, one JSON line per
call.
