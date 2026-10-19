# MCP Server Checkup Report

This report evaluates the `notes-mcp` server against the 10 failure modes outlined in the guide.

## Results Table

| Check | Result | Evidence | Fix |
|---|---|---|---|
| **C1 · The tool list answers without a token** | PASS | `initialize` returned HTTP 200 with 3 tools (`search_notes`, `get_note`, `add_note`). `server/discover` returned HTTP 200 with JSON-RPC `-32601` (`method not found: server/discover`), not 401. | — |
| **C2 · A tool refusal comes back as a result, not a protocol error** | FAIL | `tools/call` for `get_note` with non-existent id `n-999` returned JSON-RPC error `{"code": -32602, "message": "note not found: n-999"}`. Missing `id` argument returned `{"code": -32602, "message": "missing required argument: id"}`. Neither returned a tool result with `isError: true`. | [My live MCP test asserted the bug: a real client threw where my test passed](https://worklore.dev/s/2026-10-02-my-live-mcp-test-asserted-the-bug-a-real-client-threw-where-) |
| **C3 · The session survives an error** | PASS | Immediately following the `-32602` error in the same session (`Mcp-Session-Id`), a valid call to `get_note` (`id: "n-1"`) succeeded with HTTP 200 and returned note data. | — |
| **C4 · The published outputSchema is honoured** | PASS | Valid call to `get_note` returned `isError: false` and `structuredContent` matching schema with all required keys (`id`, `title`, `body`, `words`) and types. Valid call to `search_notes` returned `isError: false` with `structuredContent: {"hits": [...], "total": 1}`. | — |
| **C5 · Results survive serialisation** | PASS | All responses from C2–C4 parsed cleanly as JSON. In `get_note`, `words` is integer `17`, and `content[0].text` agrees with `structuredContent`. | — |
| **C6 · The version moves when the surface moves** | FAIL | Inspection of source repository reveals no committed surface lock file. Registry entry for `notes-mcp/0.3.1` does not exist (HTTP 404). Per C6 criteria, lack of a surface lock to prevent drift counts as FAIL (WARN). | [My MCP listing said read-only. My server could write.](https://worklore.dev/s/2026-09-30-my-mcp-listing-said-read-only-my-server-could-write) and [Getting into the MCP Registry](https://worklore.dev/s/2026-09-23-getting-into-the-mcp-registry-server-json-a-read-org-token-a) |
| **C7 · Calls are logged** | PASS | Source review (`server.py` lines 80-84, 216) and stderr logs confirm a single handler writes structured JSON lines per call: `{"t": "...", "method": "...", "tool": "...", "ok": ..., "ms": ..., "who": "..."}`, logging both successful and failed calls. | — |
| **C8 · Tool count and names** | PASS | 3 tools found: `search_notes`, `get_note`, `add_note`. All names match `^[a-zA-Z0-9_-]{1,64}$`. | — |
| **C9 · Version negotiation is honest** | PASS | Sent `initialize` with `"protocolVersion": "banana"`. Server did not echo "banana"; it answered with its implemented version `"2025-06-18"`. | — |
| **C10 · The outputSchema can reject a wrong answer** | FAIL | `search_notes` declares `outputSchema: {"type": "object"}` with no required properties or constraints, accepting corrupted result `{}`. While `get_note`'s schema rejected the corrupted result (due to `pattern: "^n-[0-9]+$"` and `minimum: 0`), C10 specifies FAIL if any declared schema accepts corrupted data. | [My MCP server's output schemas accepted wrong answers](https://worklore.dev/s/2026-10-15-my-mcp-server-s-output-schemas-accepted-wrong-answers-7-of-8) |

---

**has the problem**

### What could not be checked externally and what would unlock it:
- Official registry fingerprint comparison in **C6**: The server is not yet published in the official MCP Registry (`https://registry.modelcontextprotocol.io/v0.1/servers/notes-mcp/versions/0.3.1` returned 404). Publishing an entry with a `mcp-surface/1` publisher block would unlock registry fingerprint verification via `verify.mjs`.
