# Audit of `notes-mcp` (`server.py`): Issues That Trip Up Real MCP Clients

This report documents the protocol violations, transport quirks, authentication traps, schema mismatches, and runtime bugs in [`server.py`](file:///tmp/h-W4J6EU/server.py) that cause real-world MCP clients (such as Claude Code, Codex, Gemini CLI / Antigravity, MCP Inspector, and official TypeScript/Python MCP SDKs) to fail or misbehave.

---

## 1. Streamable HTTP Transport & Session Handling

### 1.1 Hardcoded `2025-06-18` Protocol Version (No Version Negotiation)
* **Where:** [`server.py:19`](file:///tmp/h-W4J6EU/server.py#L19), [`server.py:135-141`](file:///tmp/h-W4J6EU/server.py#L135-L141)
* **What happens:** `initialize` ignores `params.protocolVersion` from the client and unconditionally responds with `"protocolVersion": "2025-06-18"`.
* **Why clients trip:** Per the MCP specification, version negotiation requires the server to echo the client's requested version if supported, or return the latest version it supports. Clients only supporting `2024-11-05` or `2025-03-26` (when Streamable HTTP was introduced) will reject the handshake and disconnect if they do not recognize `2025-06-18`. Furthermore, the `2025-06-18` spec mandates that clients send the `MCP-Protocol-Version` HTTP header on subsequent requests, which the server neither validates nor handles.

### 1.2 `GET /mcp` Returns `405` with a JSON Body and No `Allow` Header
* **Where:** [`server.py:186-187`](file:///tmp/h-W4J6EU/server.py#L186-L187)
* **What happens:** `do_GET` returns `405` with `Content-Type: application/json` (`{"error": "use POST"}`) and omits the HTTP-mandated `Allow: POST, DELETE` header (RFC 9110 §15.5.6).
* **Why clients trip:** Streamable HTTP clients open a `GET /mcp` request with `Accept: text/event-stream` to listen for server-initiated messages/notifications. While returning `405 Method Not Allowed` is legal when a server doesn't offer a standalone SSE stream, clients/proxies that check `Allow` headers or probe `GET /.well-known/...` paths (which also hit `do_GET` and get `405` instead of `404`!) get confused—especially during OAuth discovery (see §2.2).

### 1.3 No CORS or `OPTIONS` Preflight Handling (`501 Unsupported Method`)
* **Where:** [`server.py:171-191`](file:///tmp/h-W4J6EU/server.py#L171-L191)
* **What happens:** `Handler` does not implement `do_OPTIONS` and sets no `Access-Control-Allow-*` headers (Nor `Access-Control-Expose-Headers: Mcp-Session-Id`). Also, there is no `Origin` header validation (which MCP Streamable HTTP requires to prevent DNS rebinding attacks).
* **Why clients trip:** Browser-based MCP clients (like MCP Inspector) send an `OPTIONS /mcp` preflight request with `Content-Type: application/json`, `Authorization`, `Mcp-Session-Id`, and `MCP-Protocol-Version`. `BaseHTTPRequestHandler` replies `501 Unsupported method ('OPTIONS')`, immediately blocking connection. Even if bypassed, browser clients cannot read `Mcp-Session-Id` without `Access-Control-Expose-Headers`.

### 1.4 Broken Session Lifecycle & Echoing `Mcp-Session-Id` on Every Response
* **Where:** [`server.py:180-181`](file:///tmp/h-W4J6EU/server.py#L180-L181), [`server.py:189-190`](file:///tmp/h-W4J6EU/server.py#L189-L190), [`server.py:203`](file:///tmp/h-W4J6EU/server.py#L203), [`server.py:213-214`](file:///tmp/h-W4J6EU/server.py#L213-L214)
* **What happens:**
  1. If a client doesn't send `Mcp-Session-Id` on `initialize`, a UUID is generated, returned in the header, and immediately discarded by the server (never stored).
  2. Subsequent requests don't verify that `Mcp-Session-Id` is valid or even present.
  3. `do_DELETE` returns `204` without invalidating any session, and works on any path.
  4. If the client sends `Mcp-Session-Id` on `initialize`, the server reuses the client's header instead of issuing a fresh server-generated session ID.

### 1.5 JSON-RPC Batch Requests Removed in `2025-06-18` & Broken Batch Handling
* **Where:** [`server.py:205-211`](file:///tmp/h-W4J6EU/server.py#L205-L211)
* **What happens:**
  1. The server claims protocol version `2025-06-18`, which **explicitly removed JSON-RPC batching** from MCP.
  2. Even for `2025-03-26` clients that do send batches:
     * A batch containing **only notifications** returns `200 OK` with `[]` (`Content-Type: application/json`) instead of `202 Accepted` with an empty body, violating both JSON-RPC 2.0 and MCP Streamable HTTP specs.
     * An empty batch `[]` returns `200 []` instead of JSON-RPC `-32600 Invalid Request`.
     * If `initialize` is sent inside a batch, no `Mcp-Session-Id` is generated ([`server.py:213`](file:///tmp/h-W4J6EU/server.py#L213) is skipped).
     * Sub-items in a batch that aren't dicts (e.g., `[1, "a"]`) crash the worker thread with `AttributeError: 'int' object has no attribute 'get'`.
     * If a batch contains an unauthorized `add_note` or `resources/*` call, `handle()` returns `(401, {"error": ...})`. The batch loop ignores the `401` status and appends `{"error": "sign in required"}` (which is **not** a valid JSON-RPC 2.0 response object—no `jsonrpc` or `id`, and `error` is a string instead of `{code, message}`) into the `200 OK` JSON array! Clients crash trying to parse that batch item.
     * Batch calls completely skip `log()`.

### 1.6 Other Unhandled Notifications Return `-32601 Method Not Found`
* **Where:** [`server.py:142-143`](file:///tmp/h-W4J6EU/server.py#L142-L143), [`server.py:168`](file:///tmp/h-W4J6EU/server.py#L168)
* **What happens:** Only `notifications/initialized` returns `202`. Any other client notification—such as `notifications/cancelled` (sent when a user cancels a tool call or hits a timeout), `notifications/roots/list_changed`, or `notifications/progress`—has `id: None` and falls through to `rpc_error(None, -32601, "method not found: ...")` with HTTP `200`.
* **Why clients trip:** In JSON-RPC 2.0, servers **MUST NOT** reply to notifications (requests without an `id`), and in MCP Streamable HTTP, notifications must return `202 Accepted` with no body. Returning a `200` JSON-RPC error with `"id": null` for `notifications/cancelled` causes strict JSON-RPC/MCP clients to throw an unmatched response error or abort the transport.

### 1.7 Chunked Transfer-Encoding & Missing `Content-Length` Silently Treated as Empty `{}`
* **Where:** [`server.py:195-198`](file:///tmp/h-W4J6EU/server.py#L195-L198)
* **What happens:** `n = int(self.headers.get("Content-Length") or 0)`. If a client uses `Transfer-Encoding: chunked` (no `Content-Length`), `n` is `0`, `raw` is `b""`, and `raw or b"{}"` parses as `{}`! That then calls `handle({}, who)` which returns HTTP `200` with `{"jsonrpc": "2.0", "id": null, "error": {"code": -32601, "message": "method not found: None"}}` (instead of `-32600 Invalid Request`), leaving the actual request body unread on the socket and corrupting HTTP keep-alive Framing (`HTTP/1.1` connections).

---

## 2. Authentication & OAuth Discovery Traps

### 2.1 Mixed Anonymous + Authenticated Endpoints Break Real MCP OAuth Clients
* **Where:** [`server.py:148-150`](file:///tmp/h-W4J6EU/server.py#L148-L150), [`server.py:165-166`](file:///tmp/h-W4J6EU/server.py#L165-L166)
* **What happens:** `initialize`, `notifications/initialized`, `ping`, `tools/list`, and read-only `tools/call` (`search_notes`, `get_note`) succeed **without** an `Authorization` header (`200 OK`), while `resources/list`, `resources/read`, `resources/templates/list`, and `tools/call` (`add_note`) return **HTTP `401`** without a `WWW-Authenticate` header and with a non-JSON-RPC payload (`{"error": "unauthorized"}` or `{"error": "sign in required"}`).
* **Why clients trip:**
  1. **Missing `WWW-Authenticate` header:** MCP's authorization spec (both `2025-03-26` and `2025-06-18`, per RFC 9728) requires a `401 Unauthorized` response to include a `WWW-Authenticate: Bearer resource_metadata="..."` header. Without it, clients like Claude Code and MCP SDKs cannot discover how to authenticate.
  2. **OAuth discovery returns `405 Method Not Allowed`:** When an MCP client receives `401`, it immediately requests `GET /.well-known/oauth-protected-resource` and `GET /.well-known/oauth-authorization-server`. Because `do_GET` unconditionally returns `405 {"error": "use POST"}` for **all** paths, the client's OAuth flow crashes with an unexpected `405` error instead of `404` or valid metadata.
  3. **Mid-session `401` during `resources/list` or `add_note`:** Because `initialize` and `tools/list` succeed anonymously—and `initialize` advertises `"resources": {"subscribe": False, "listChanged": False}` in `capabilities`—clients automatically call `resources/list` right after initialization. That call hits a hard HTTP `401`, causing clients that eagerly fetch capabilities on startup to mark the entire MCP server connection as failed or enter an infinite re-auth loop.
  4. **Non-JSON-RPC 401 body on `add_note`:** If a client isn't configured for OAuth, calling `add_note` returns HTTP `401` with `{"error": "sign in required"}` instead of either a valid JSON-RPC error or a tool result with `isError: true`. Many HTTP transports throw a low-level transport/parse exception rather than letting the LLM know that `add_note` requires authentication.

---

## 3. Tool Definitions, `outputSchema`, & Execution Errors

### 3.1 `search_notes` Incomplete `outputSchema`
* **Where:** [`server.py:34`](file:///tmp/h-W4J6EU/server.py#L34), [`server.py:112`](file:///tmp/h-W4J6EU/server.py#L112)
* **What happens:** `search_notes` declares `"outputSchema": {"type": "object"}` with no `properties` or `required` fields, even though it returns `structuredContent: {"hits": [...], "total": ...}`.
* **Why clients trip:** In MCP `2025-06-18`, `outputSchema` is used by clients and LLMs to know the structure of `structuredContent` and validate it. Furthermore, `text` content returns `json.dumps(hits)` (a JSON **array** `[{...}]`), whereas `structuredContent` is an **object** `{"hits": hits, "total": len(hits)}`—so the serialized text representation and `structuredContent` don't even have the same shape! (Also, `"total": len(hits)` is calculated *after* `hits = hits[:limit]`, so `total` is just the truncated count rather than total matches).

### 3.2 `get_note` Violates Its Own `outputSchema` When `tags` Contains Empty Strings or `title` Is Empty, and Returns `-32602` Instead of `isError: true`
* **Where:** [`server.py:45-55`](file:///tmp/h-W4J6EU/server.py#L45-L55), [`server.py:113-121`](file:///tmp/h-W4J6EU/server.py#L113-L121), [`server.py:163-164`](file:///tmp/h-W4J6EU/server.py#L163-L164)
* **What happens:**
  1. When `get_note` is called with a valid ID format that doesn't exist (e.g., `{"id": "n-999"}`), `call_tool` raises `ValueError("note not found: n-999")`, which `handle()` converts into a **JSON-RPC protocol error `-32602`** (`Invalid params`).
  2. **Why clients trip:** The MCP specification explicitly states that **tool execution/business errors** (like a missing record `"note not found: n-999"`) should be returned inside the result with `"isError": true` (`tool_result("note not found: n-999", is_error=True)`), **NOT** as a JSON-RPC protocol error (`-32602`). Wait: even worse, when a tool declares an `outputSchema` in MCP `2025-06-18`, clients validate `structuredContent` unless `isError: true`. By returning a protocol-level `-32602`, many clients treat it as a fatal client bug or schema failure rather than allowing the LLM to see that note `n-999` doesn't exist and recover.

### 3.3 Missing Input Validation Causes Unhandled `500` / Connection Drops Instead of Clean Errors
* **Where:** [`server.py:102-128`](file:///tmp/h-W4J6EU/server.py#L102-L128), [`server.py:157-164`](file:///tmp/h-W4J6EU/server.py#L157-L164)
* **What happens:** The server exposes JSON Schemas (`inputSchema`) with constraints (`required`, `pattern`, `minimum`, `maximum`, `minLength`, `type`), **but never validates incoming `arguments` against `inputSchema`**!
  * **`add_note` missing `title` or `body`:** `args["title"]` or `args["body"]` raises `KeyError`, which is **not** caught by `except ValueError:`. `BaseHTTPRequestHandler` catches the unhandled exception, aborts the response or sends an HTML `500` error page, and crashes the request!
  * **`add_note` with empty `title: ""` or non-string `title` / `body`:** `add_note` accepts `{"title": "", "body": "..."}` even though `inputSchema` has `minLength: 1`. Later, when `get_note` is called on that new note, `get_note`'s `outputSchema` requires `"title": {"type": "string", "minLength": 1}`! Every strict MCP `2025-06-18` client (like the official TypeScript/Python SDKs) validates `structuredContent` against `outputSchema` and **throws a client-side validation error** when reading back the note with an empty title!
  * **`add_note` with non-string `body` (e.g. `123` or `null`):** Succeeds in `add_note`, then crashes `search_notes` (`TypeError: can only concatenate str (not "int") to str`) and `get_note` (`AttributeError: 'int' object has no attribute 'split'`) for the rest of the server's lifetime!
  * **`search_notes` with `limit <= 0`, `limit > 50`, or `limit: null`:** `args.get("limit", 10)` returns `None` if the client explicitly passes `{"query": "soil", "limit": null}`, raising `TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'` (unhandled crash). Negative `limit` (e.g., `limit: -1`) slices `hits[:-1]`, silently dropping the last search hit instead of rejecting `limit < 1`! And missing `query` (`{}`) defaults to `""`, which matches every note at index `0` instead of rejecting the missing required field.
  * **`get_note` with invalid `id` pattern (e.g. `"1"`):** Not validated against `^n-[0-9]+$`.
  * **`params` or `arguments` passed as a non-dict (e.g. list or primitive):** Crashes with `AttributeError`.

### 3.4 `search_notes` Snippet Bug When Match Is in the Title
* **Where:** [`server.py:107-110`](file:///tmp/h-W4J6EU/server.py#L107-L110)
* **What happens:**
  ```python
  text = (n["title"] + " " + n["body"]).lower()
  if q in text:
      i = text.find(q)
      hits.append({"id": n["id"], "title": n["title"], "snippet": n["body"][max(0, i - 30): i + 50]})
  ```
  `i` is the character index in `title + " " + body`, **not** the index in `body`!
* **Why clients/LLMs trip:**
  * When `q` matches in the `body`, the slice index in `n["body"]` is shifted right by `len(n["title"]) + 1` characters, cutting off the match or shifting the window past it.
  * If `n["title"]` is long and `n["body"]` is short (e.g., `i - 30 > len(n["body"])`), `snippet` is completely empty (`""`) even though the note matched!
  * Also, `.lower()` can change string length for some Unicode characters (e.g. `İ`), causing `i` in `text` to misalign with `n["body"]`.

---

## 4. Resources & Protocol Bugs

### 4.1 `resources/read` Ignores `params.uri`
* **Where:** [`server.py:148-155`](file:///tmp/h-W4J6EU/server.py#L148-L155)
* **What happens:** `resources/read` never inspects `params.get("uri")`. Whether a client requests `notes://guide`, `notes://nonexistent`, or omits `uri` altogether, the server always returns `notes://guide`.
* **Why clients trip:** According to the MCP spec, if `params.uri` is missing, the server should return `-32602` (Invalid params), and if the URI is unknown, it should return error code `-32002` (Resource not found).

### 4.2 Added Notes Are Not Exposed as Resources and Are Not Persisted or Thread-Safe
* **Where:** [`server.py:22-23`](file:///tmp/h-W4J6EU/server.py#L22-L23), [`server.py:125-126`](file:///tmp/h-W4J6EU/server.py#L125-L126), [`server.py:224`](file:///tmp/h-W4J6EU/server.py#L224)
* **What happens:**
  * `ThreadingHTTPServer` spawns a thread per request, and `add_note` computes `nid = f"n-{max(int(k[2:]) for k in NOTES) + 1}"` and mutates the global `NOTES` dict without a lock while `search_notes` iterates `for n in NOTES.values():`. Concurrent `add_note` and `search_notes` calls can raise `RuntimeError: dictionary changed size during iteration` or overwrite each other's generated IDs.
  * `NOTES` is only held in memory (`notes.json` is never updated on `add_note`), so restarting the server loses all added notes.

---

## 5. Summary Table

| Category | Location | Issue | Client Symptom |
| :--- | :--- | :--- | :--- |
| **Transport / HTTP** | `server.py:186-187` | `GET` returns `405` on all paths (`/.well-known/*`, `/mcp`) without `Allow` header | OAuth discovery & SSE stream probes fail unexpectedly |
| **Transport / CORS** | `server.py:171-191` | No `do_OPTIONS`, no CORS headers, no `Origin` check | Browser clients (MCP Inspector) fail with `501 Unsupported method ('OPTIONS')` |
| **Transport / Framing** | `server.py:195-198` | Missing `Content-Length` / chunked encoding reads `0` bytes and parses `{}` | Returns `-32601 method not found: None` and corrupts keep-alive socket |
| **Protocol Version** | `server.py:19, 137` | Hardcoded `2025-06-18`; ignores client `protocolVersion` and `MCP-Protocol-Version` header | Older clients (`2024-11-05`, `2025-03-26`) reject handshake |
| **Notifications** | `server.py:142, 168` | Only `notifications/initialized` returns `202`; `notifications/cancelled` etc. return `200` with JSON-RPC error | Clients throw unmatched response / protocol error on cancellation |
| **JSON-RPC Batching** | `server.py:205-211` | Batching forbidden in `2025-06-18`; notification-only batch returns `200 []`; 401 in batch injects non-JSON-RPC dict | Invalid JSON-RPC batch response crashes client parser |
| **Auth / OAuth** | `server.py:149-150, 165-166` | Open `initialize`/`tools/list` + sudden HTTP `401` on `resources/list` & `add_note` with no `WWW-Authenticate` header | Clients fail right after `initialize` when auto-listing resources or cannot trigger OAuth flow |
| **Tool Errors** | `server.py:118-119, 163-164` | `get_note` missing ID returns JSON-RPC `-32602` instead of `isError: true` tool result | LLM cannot self-correct on missing note ID; client treats as protocol/param error |
| **Schema / Validation** | `server.py:34, 102-128` | `search_notes` `outputSchema` is bare `{"type": "object"}` & `text` vs `structuredContent` mismatch; `inputSchema` is unvalidated | Unhandled `KeyError`/`TypeError` crashes request (`500`); `add_note` with `title=""` breaks `get_note` `outputSchema` validation |
| **Resources** | `server.py:148-155` | `resources/read` ignores `params.uri` | Always returns `notes://guide` even for invalid/missing URIs |
| **Logic / Concurrency** | `server.py:107-110, 125-126` | `search_notes` snippet uses `title + " " + body` offset to slice `body`; unlocked `NOTES` dict in `ThreadingHTTPServer` | Wrong/empty search snippets; `RuntimeError` under concurrent requests |
