# MCP checkup: notes-mcp (127.0.0.1:49514/mcp)

**Verdict: has the problem.** Three checks fail: C2 (refusals come back as JSON-RPC errors), C6 (no surface lock and no registry entry, so nothing stops drift), and C10 (the `search_notes` output schema accepts a wrong answer).

Scope: the checkup ran against the server started from this folder, with no token. Every check that needs a read was possible anonymously, because the read tools are open. `add_note` was never called, not even with fake arguments, so its signed-in path is not covered. Nothing in the repository was changed.

## Results

| Check | Result | Evidence | Fix |
|---|---|---|---|
| C1 · tool list without a token | PASS | `initialize` → 200, `protocolVersion 2025-06-18`, `Mcp-Session-Id` issued. `tools/list` → 200, 3 tools. `server/discover` → 200 `{"error":{"code":-32601,"message":"method not found: server/discover"}}` | — |
| C2 · refusal as result, not error | **FAIL** | `get_note {"id":"n-999"}` → 200 `{"error":{"code":-32602,"message":"note not found: n-999"}}`. `get_note {}` → 200 `{"error":{"code":-32602,"message":"missing required argument: id"}}`. Both are `error`, not `result` with `isError: true`. | [My live MCP test asserted the bug: a real client threw where my test passed](https://worklore.dev/s/2026-10-02-my-live-mcp-test-asserted-the-bug-a-real-client-threw-where-) |
| C3 · session survives an error | PASS | Same `Mcp-Session-Id` as C2, right after the refusals: `search_notes {"query":"compost","limit":5}` → 200, `isError: false`, 1 hit. | — (same story as C2) |
| C4 · outputSchema honoured | PASS | `search_notes {"query":"frost"}` → 200, `isError: false`, `structuredContent {"hits":[…],"total":1}`, validates against `{"type":"object"}`. `get_note {"id":"n-2"}` → 200, `isError: false`, `structuredContent` with `id/title/body/words/tags`, validates against its schema. | — |
| C5 · results survive serialisation | PASS | Every body in C2–C4 parses as JSON. For both successful calls, `content[0].text` parses to the same object as `structuredContent`. No encoder errors, no numbers-as-strings. | — |
| C6 · version moves with the surface | **FAIL (WARN)** | No registry entry: README says "Not yet listed in any registry", and a registry search for `notes-mcp` returned 14 entries, none of them this server, with no `mcp-surface/1` block. Source present, no surface lock: the repo holds only `server.py`, `README.md`, `notes.json`, with no test and no CI. Lists do not change by themselves (one static resource, empty templates). Fingerprint computed by the spec §2–§3 for `serverInfo.version` `0.3.1`: `sha256 55354fc1d1a10a403c32fe5390c6d6fdded5a24a34575a1c596c0b9517b523c2` (anonymous capture; `resources`, `resourceTemplates`, `prompts` not served anonymously, so `null`). | [My MCP listing said read-only. My server could write.](https://worklore.dev/s/2026-09-30-my-mcp-listing-said-read-only-my-server-could-write), and for the registry entry [Getting into the MCP Registry](https://worklore.dev/s/2026-09-23-getting-into-the-mcp-registry-server-json-a-read-org-token-a) |
| C7 · calls are logged | PASS, with gaps | `log()` runs once per single JSON-RPC call and writes one JSON line to stderr with `method`, `tool`, `ok`, `ms`, `who`. Errors are logged with `ok:false` (seen for both `get_note` refusals). Gaps: a two-call batch produced **no** lines; a malformed body (400) produces none; `who` is only `anon` or `dev`, and `dev` is one shared token, so it does not identify a user. | — |
| C8 · tool count and names | PASS | 3 tools: `search_notes`, `get_note`, `add_note`. All match `^[a-zA-Z0-9_-]{1,64}$`. | — |
| C9 · honest version negotiation | PASS | `initialize` with `"protocolVersion":"banana"` → 200, `protocolVersion: "2025-06-18"`. Fixed value, not an echo. | — |
| C10 · outputSchema rejects a wrong answer | **FAIL** (`search_notes`) | `search_notes` declares `outputSchema: {"type":"object"}` with no `required` and no `properties`. The corrupted instance `{}` is **accepted**. `get_note`: corrupted instance rejected by `minimum` on `words`. `add_note`: rejected by `pattern` on `id`. Validated with `jsonschema` 4.26.0 from `tools/list` only; `add_note` was not called. | [My MCP server's output schemas accepted wrong answers (7 of 8)](https://worklore.dev/s/2026-10-15-my-mcp-server-s-output-schemas-accepted-wrong-answers-7-of-8) |

## Outside the ten checks

- **Default token in source.** `server.py` falls back to `NOTES_TOKEN` default `dev-token-123`, and the README documents it. If the server is ever run without that env var set, anyone can call `add_note`. This is not one of the ten checks, but it is the most serious item here.
- **Resources advertised, then 401.** `initialize` advertises `resources`, but anonymous `resources/list` and `resources/templates/list` return `401 {"error":"unauthorized"}`. This is the case your worklore intro describes. The fix is the same shape: answer anonymously with public items only.

## Not checked, and what would unlock it

- **Signed-in path** (`add_note`, and `resources/*` with a token). Not needed for the ten checks. To run it: set `NOTES_TOKEN` in the environment and never print it. Calling `add_note` writes to the in-memory note list, so it needs your go-ahead first.
- **C6 registry comparison.** Would need a published registry entry under a known name. The source-side lock check was done: there is no lock.
- **C6 fingerprint with a token.** The hash above is the anonymous capture. A signed-in capture would include `resources/list`, so it would differ. The spec says to publish the anonymous one.
- **C7 logs.** Source was read and the stderr log was captured from this run. Production logs were not available.

## Recording

No worklore tool is available in this session, so the result was not recorded. The result to record, if the check applies to you and is complete, is `has_problem`. It is complete: C2–C5 all ran.
