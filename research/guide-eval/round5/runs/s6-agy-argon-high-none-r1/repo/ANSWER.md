# Issues Real MCP Clients Trip Over in `server.py`

Below is a categorized audit of what breaks or misbehaves when connecting real MCP clients (Claude Code, OpenAI Codex, Gemini CLI, MCP Inspector, and the official TypeScript/Python MCP SDKs) to `server.py`.

---

## 1. Authentication, OAuth Discovery, and Mixed Anonymous/Authenticated Flow

1. **Advertising `resources` and `add_note` to anonymous sessions, then failing mid-session with raw HTTP `401` (`server.py:135-141`, `146-150`, `165-166`)**
   - `initialize` and `tools/list` succeed without an `Authorization` header and advertise `"capabilities": {"resources": ...}` plus the `add_note` tool.
   - Many clients (including Claude Code, Codex, and Gemini CLI) automatically call `resources/list` (and `resources/templates/list`) immediately after `initialize` when the `resources` capability is declared. Because the anonymous handshake succeeded, `resources/list` immediately fails with HTTP `401 {"error": "unauthorized"}`, which causes clients to mark the server as failed/disconnected or enter an OAuth flow before the user can even use the open read tools (`search_notes`, `get_note`).
   - Likewise, exposing `add_note` in `tools/list` to anonymous users invites the model to call it, which triggers a transport-level HTTP `401 {"error": "sign in required"}` instead of a tool error (`isError: true`) or JSON-RPC error.

2. **Missing `WWW-Authenticate` header on `401` and `405` on OAuth discovery endpoints (`server.py:149-150`, `165-166`, `174-187`)**
   - Per the MCP `2025-06-18` Authorization spec (RFC 9728 / OAuth 2.1), a `401 Unauthorized` response must include a `WWW-Authenticate` header (e.g., `Bearer resource_metadata="..."`). `_send()` sends no `WWW-Authenticate` header.
   - When standard MCP clients receive an HTTP `401`, they attempt OAuth discovery via `GET /.well-known/oauth-protected-resource` and `GET /.well-known/oauth-authorization-server`. Because `do_GET` unconditionally returns `405 {"error": "use POST"}` for **every** path (`server.py:186-187`), OAuth discovery fails with `405 Method Not Allowed` instead of `404` or valid metadata.

3. **Invalid or differently formatted `Authorization` headers silently downgrade to `"anon"` (`server.py:201-202`)**
   - `who = "dev" if auth == f"Bearer {TOKEN}" else "anon"` performs an exact string comparison.
   - If a client configures a wrong token, lowercase scheme (`bearer dev-token-123`, valid per RFC 9110), or extra whitespace, `initialize` and read calls silently succeed as `"anon"` instead of rejecting the bad credentials upfront.

4. **Non-JSON-RPC error bodies on HTTP `400`/`401`/`404`/`405` (`server.py:150`, `166`, `187`, `194`)**
   - Responses like `{"error": "unauthorized"}` and `{"error": "sign in required"}` use a string for `"error"` and omit `"jsonrpc": "2.0"` and `"id"`. Clients that parse JSON bodies on error responses as JSON-RPC `JSONRPCError` objects (`error: {code, message}`) fail schema validation (e.g., Zod errors in `@modelcontextprotocol/sdk`).

---

## 2. MCP Lifecycle, Protocol Negotiation, and Notifications

1. **No protocol version negotiation in `initialize` (`server.py:19`, `135-141`)**
   - `initialize` ignores `params["protocolVersion"]` and always returns `"protocolVersion": "2025-06-18"`.
   - Per the MCP spec, if a client only supports an earlier version (such as `"2024-11-05"` or `"2025-03-26"`) and receives `"2025-06-18"`, the client **must disconnect immediately**.
   - Conversely, for `"2025-06-18"` clients, the server never checks or validates the `MCP-Protocol-Version` HTTP header on subsequent requests.

2. **All notifications other than `notifications/initialized` return HTTP `200` with a JSON-RPC error (`server.py:142-143`, `168`)**
   - Only `notifications/initialized` returns `202, None`.
   - Standard client notifications such as `notifications/cancelled` (sent when a request times out or is aborted by the user), `notifications/roots/list_changed`, or `notifications/progress` fall through to line 168 and return HTTP `200` with `{"jsonrpc": "2.0", "id": null, "error": {"code": -32601, "message": "method not found: ..."}}`.
   - Both JSON-RPC 2.0 and MCP Streamable HTTP forbid returning JSON-RPC responses to notifications (messages without an `"id"`); Streamable HTTP requires `202 Accepted` with no body. SDK clients reject or error on unexpected `id: null` error responses.

---

## 3. Streamable HTTP Transport, Sessions, and Batching

1. **Sessions (`Mcp-Session-Id`) are never tracked or invalidated (`server.py:180-181`, `189-190`, `203`, `213-214`)**
   - `initialize` generates a `Mcp-Session-Id` header (unless the client already sent one, in which case it echoes the client's value), but the server never stores active session IDs.
   - `do_DELETE` returns `204` on any path without invalidating the session. Under the Streamable HTTP spec, requests using a terminated or unknown `Mcp-Session-Id` must receive `404 Not Found` so clients know to re-initialize.

2. **Broken JSON-RPC batch handling (and batching is removed in `2025-06-18`) (`server.py:205-211`)**
   - MCP `2025-06-18` removed JSON-RPC batching.
   - For `2025-03-26` clients that send batches (`isinstance(req, list)`):
     - Per-item HTTP status codes are discarded (`_, b = handle(r, who)`), so a `401` on `resources/list` or `add_note` is wrapped inside a `200 OK` batch array as `{"error": "unauthorized"}` (an invalid JSON-RPC batch item with no `jsonrpc` or `id`).
     - A notification-only batch returns `200 OK` with `[]` instead of `202 Accepted` with an empty body.
     - An empty batch `[]` returns `200 OK` with `[]` instead of `-32600 Invalid Request`.
     - If `initialize` is sent inside a batch, no `Mcp-Session-Id` is generated (lines 213-214 are skipped), and batch requests are never logged.

3. **HTTP parsing, routing, and CORS gaps (`server.py:171-218`)**
   - **Query strings break routing (`server.py:193`)**: `self.path.rstrip("/") != "/mcp"` fails with `404` if a client or proxy includes query parameters (e.g., `/mcp?session=...`). Meanwhile `do_GET` and `do_DELETE` don't check `self.path` at all.
   - **Chunked transfer encoding (`server.py:195-196`)**: `int(self.headers.get("Content-Length") or 0)` reads `0` bytes when a client sends `Transfer-Encoding: chunked`, treating the body as `{}` (`method not found: None`) and leaving unread bytes on the socket.
   - **HTTP/1.0 default (`server.py:171`)**: `BaseHTTPRequestHandler` defaults to `HTTP/1.0` (`protocol_version = "HTTP/1.1"` is not set), closing connections after each request.
   - **No `Allow` header on `405` (`server.py:186-187`)**: `do_GET` returns `405` without the RFC-required `Allow: POST, DELETE` header.
   - **No CORS / `OPTIONS` support**: Browser-based clients (such as MCP Inspector) send `OPTIONS /mcp` preflight requests, which fail with `501 Unsupported method ('OPTIONS')`, and `Access-Control-Expose-Headers: Mcp-Session-Id` is missing.
   - **Non-object JSON bodies crash the handler (`server.py:198`, `132`, `134`, `216`)**: Sending a JSON primitive (`123`, `"str"`, `null`) or a request with non-dict `"params"` (e.g., `"params": []`) raises `AttributeError: ... object has no attribute 'get'`, crashing the request thread without a response.

---

## 4. Tool Schemas, `structuredContent`, and Tool Execution Bugs

1. **`add_note` crashes the HTTP connection on missing arguments (`server.py:126`, `161-164`)**
   - `call_tool("add_note", ...)` indexes `args["title"]` and `args["body"]` directly, while `handle()` only catches `ValueError`.
   - If a client omits `title` or `body`, Python raises `KeyError`, crashing `do_POST` before `_send()` runs and dropping the TCP connection (`RemoteDisconnected` / `ECONNRESET`).

2. **`search_notes` has an incomplete `outputSchema` and mismatched `text` vs `structuredContent` (`server.py:34`, `112`)**
   - `outputSchema` is `{"type": "object"}` with no `properties`. Strict schema validators (notably Gemini function declaration / schema validators and OpenAI/Codex strict schema converters) reject `type: "object"` schemas without `properties` (or `additionalProperties: false`).
   - `call_tool` returns `tool_result(json.dumps(hits), {"hits": hits, "total": len(hits)})`: `content[0].text` is a serialized JSON **array** (`[...]`), whereas `structuredContent` is a JSON **object** (`{"hits": [...], "total": ...}`). Per MCP `2025-06-18`, the fallback `TextContent` block should serialize the same structure as `structuredContent`.
   - `"total": len(hits)` is computed *after* `hits = hits[:limit]` (`server.py:111-112`), so `total` only reflects the truncated slice length rather than total matches.

3. **`search_notes` snippet slicing uses the wrong string offset (`server.py:107-110`)**
   - `i = text.find(q)` finds the match index in `n["title"] + " " + n["body"]`, but slices `n["body"][max(0, i - 30): i + 50]`.
   - Because `i` is shifted by `len(n["title"]) + 1`, snippets are cut at the wrong offset (e.g., searching `"liming"` in `n-1` yields `"d, not for liming decisions."`), matches in the title return the beginning of `body`, and matches near the end of a note with a long title can slice past `len(n["body"])` and return `""`.

4. **`get_note` returns JSON-RPC protocol errors (`-32602`) instead of tool execution errors (`isError: true`) (`server.py:94-98`, `118-119`, `163-164`)**
   - Looking up a non-existent note (e.g., `{"id": "n-999"}`) raises `ValueError("note not found: n-999")`, which `handle()` converts into a JSON-RPC `-32602` error.
   - Per the MCP spec, runtime/domain errors in `tools/call` should return a tool result with `"isError": true` so the LLM can read the error and self-correct; returning a JSON-RPC error causes clients to treat it as a protocol failure. (`tool_result` defines `is_error=False` on line 94, but `is_error=True` is never used.)

5. **Unenforced `inputSchema` constraints can corrupt state and break `get_note` `outputSchema` validation (`server.py:29-70`, `102-127`)**
   - `add_note` does not check `minLength: 1` on `title` or verify that `title` and `body` are strings.
   - If `add_note` is called with `title: ""`, it succeeds, but subsequently calling `get_note` on that note returns `structuredContent` with `title: ""`, which violates `get_note`'s `outputSchema` (`"title": {"type": "string", "minLength": 1}`) and causes MCP `2025-06-18` SDK clients to throw client-side output validation errors.
   - If `add_note` is called with non-string `title` or `body` (e.g., `null` or an integer), every future call to `search_notes` (`n["title"] + " " + n["body"]`) or `get_note` (`n["body"].split()`) crashes with an unhandled `TypeError`/`AttributeError`.
   - Passing `limit: null` to `search_notes` or a list/dict `id` to `get_note` also raises an unhandled `TypeError`, dropping the connection.

6. **Race condition and non-persistence in `add_note` (`server.py:125-126`, `224`)**
   - `ThreadingHTTPServer` processes requests on concurrent threads, and `nid = f"n-{max(int(k[2:]) for k in NOTES) + 1}"` mutates the global `NOTES` dict without a lock (and never persists changes to `notes.json`).

---

## 5. Resources Endpoint Bugs

1. **`resources/read` ignores `params.uri` (`server.py:148-155`)**
   - `resources/read` never inspects `params.get("uri")`. Calling `resources/read` with an unknown URI (e.g., `notes://n-1` or `notes://nonexistent`) or no `uri` parameter at all still returns `200 OK` with the `notes://guide` payload instead of returning JSON-RPC error `-32002` (Resource not found) or `-32602` (Invalid params).
