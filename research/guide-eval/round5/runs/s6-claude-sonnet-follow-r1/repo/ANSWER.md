# MCP checkup: notes-mcp 0.3.1 (http://127.0.0.1:51860/mcp)

I ran this on 2026-10-18 with no token. Every request was read-only: `initialize`, `ping`, `server/discover`, `tools/list`, `resources/list`, `prompts/list`, and `tools/call` on `get_note` and `search_notes`, which are both marked `readOnlyHint: true`. I never called `add_note`. I didn't change `server.py`. The server wasn't running when I started, so I started it myself and stopped it afterwards.

| Check | Result | Evidence | Fix |
|---|---|---|---|
| C1 tool list without a token | PASS | `initialize` returned 200 and `tools/list` returned 200 with 3 tools. `server/discover` returned 200 with a `-32601` error, which counts as a pass. | |
| C2 refusal is a result | **FAIL** | `get_note {"id":"n-99999"}` returned 200 with a JSON-RPC `error`: `-32602 "note not found: n-99999"`. `get_note {}` returned `-32602 "missing required argument: id"`. Neither has `result.isError`. The cause is `raise ValueError` turned into `rpc_error` in `handle()`. | [My live MCP test asserted the bug](https://worklore.dev/s/2026-10-02-my-live-mcp-test-asserted-the-bug-a-real-client-threw-where-) |
| C3 session survives an error | PASS | In the same session (`Mcp-Session-Id` sent back), `search_notes` and `get_note n-1` returned normal results right after both refusals. `ping` also worked. | |
| C4 outputSchema honoured | PASS, with a caveat | `get_note` returned `isError:false` and a `structuredContent` that matches its schema. `search_notes` also returned a `structuredContent` object (`{hits,total}`), but its schema is only `{"type":"object"}`, so passing proves nothing (see C10). | |
| C5 serialisation | PASS, with a note | Every body parsed as JSON and no encoder errors appeared. One inconsistency: for `search_notes` the `content` text is a bare array `[...]`, while `structuredContent` is `{"hits":[...],"total":N}`. The data is the same but the shape differs. | |
| C6 version moves with the surface | **FAIL (WARN)** | The README says the server is in no registry, so there is no Registry entry to compare. There is no committed surface lock, no test and no CI, so nothing stops the next drift. Live `serverInfo.version` is `0.3.1`. I did not compute the `mcp-surface/1` fingerprint. Related finding: `initialize` advertises `resources`, but anonymous `resources/list` returns **401** (as do `resources/read` and `resources/templates/list`). `resources/templates/list` returns an empty list for signed-in callers. | [My MCP listing said read-only. My server could write.](https://worklore.dev/s/2026-09-30-my-mcp-listing-said-read-only-my-server-could-write) and [Getting into the MCP Registry](https://worklore.dev/s/2026-09-23-getting-into-the-mcp-registry-server-json-a-read-org-token-a) |
| C7 calls are logged | **FAIL (partial)** | Source and log both read. Single requests get one JSON line on stderr with method, tool, ok, ms and who, and errors are logged with `ok:false`. I saw 12 lines for my 12 requests. However, the JSON-RPC batch branch in `do_POST` returns before `log()`, so batched calls are never logged. | [Your MCP server is one URL](https://worklore.dev/s/2026-09-23-your-mcp-server-is-one-url-getting-per-tool-per-user-analyti) |
| C8 tool count and names | PASS | 3 tools: `search_notes`, `get_note`, `add_note`. All match `^[a-zA-Z0-9_-]{1,64}$`. | |
| C9 version negotiation | PASS | `protocolVersion:"banana"` returned `2025-06-18`, a version the server implements. It did not echo "banana". | |
| C10 outputSchema can reject a wrong answer | **FAIL** | `search_notes` has `outputSchema: {"type":"object"}`, and the corrupted result `{}` is accepted. For `get_note`, the corrupted result `{"id":"mcp-drill-corruption",...,"words":-999999999}` is rejected by the `pattern` and `minimum` constraints. `add_note`'s `id` pattern also rejects. I checked these by reading the schemas, not with a validator library. | [My MCP server's output schemas accepted wrong answers](https://worklore.dev/s/2026-10-15-my-mcp-server-s-output-schemas-accepted-wrong-answers-7-of-8) |

Verdict: **has the problem.** C2, C6, C7 and C10 are FAIL.

C4 and C5 also pass only partly. Fix `search_notes`' schema and align its `content` text with `structuredContent`.

## Not checked, and what would unlock it
- **C6 Registry comparison and fingerprint:** I need the Registry name, or a decision to publish. I also didn't run `verify.mjs` or compute the hash.
- **Signed-in behaviour (`add_note`, signed-in `resources/*`):** this was out of scope for a read-only run. `add_note` isn't read-only, so I didn't call it. For anonymous callers it returns a bare HTTP 401 instead of a tool result.
- The C10 check by reading the schemas should be repeated with `jsonschema` or `mcp-drill` for a firm result.

## Verify
- All ten checks are above.
- No writing tool was called.
- `server.py` is unchanged, and no token was used or printed.
