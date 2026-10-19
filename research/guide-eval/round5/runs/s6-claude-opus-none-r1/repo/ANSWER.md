# notes-mcp: what real MCP clients will trip over

I read `server.py` and ran it locally (`python3 server.py`, port 52312), then
sent it hand-written JSON-RPC requests with curl. I didn't change the server.
Every result marked **(observed)** was reproduced against the running process.
The rest come from reading the code. Line numbers refer to `server.py`.

## High: breaks or derails a client session

### 1. HTTP 401 is used as a per-call "permission denied" (L155-156, L163-166)
- Anonymous `resources/list`, `resources/read` and `resources/templates/list`
  return `HTTP 401 {"error":"unauthorized"}` **(observed)**.
- Anonymous `tools/call add_note` returns `HTTP 401 {"error":"sign in required"}`
  **(observed)**.

In Streamable HTTP, a 401 means the transport is unauthenticated. MCP
SDK-based clients (Claude Code, Codex and Gemini CLI all use one) respond by
running the OAuth flow or by marking the whole server "needs authentication".
They don't read it as "this one call was refused", so the read-only tools stop
working along with the write.

Two things make this worse:
- `initialize` advertises the `resources` capability to anonymous clients.
  Clients that list resources right after connecting get a 401 during startup.
- None of the 401s has a `WWW-Authenticate` header. There is no
  `/.well-known/oauth-protected-resource` endpoint either: every GET returns
  `405 {"error":"use POST"}` **(observed)**. OAuth discovery therefore can't
  succeed, and the client ends up in a failed or "needs auth" state.

The 401 bodies are also not JSON-RPC (no `jsonrpc` or `id`), so the client
can't match them to a request.

**Fix direction:** decide auth at the connection level. Either require the
bearer token for every request (clients send it from static header config), or
keep anonymous access and return
`{"result":{"isError":true,"content":[{"type":"text","text":"sign in required"}]}}`
for `add_note`. Only advertise `resources` to clients that can use it.

### 2. Bad arguments crash the request handler, and the client gets no response (observed)
An unhandled exception goes to `socketserver`'s default error handler. That
handler prints a traceback and closes the socket without writing a response.
The client sees "socket hang up" or "fetch failed", which is often treated as a
dead server. These crashes are also missing from the JSON log, because `log()`
runs after `handle()`.

Reproduced:

| Request | Exception |
|---|---|
| `search_notes` with `"limit": null` | `TypeError` in `int(None)` (L104) |
| `add_note` without `body` (authenticated) | `KeyError: 'body'` (L126) |
| `get_note` with `"arguments": ["n-1"]` (not an object) | `AttributeError` (L114) |
| Request body `null` (or any non-object, non-array JSON) | `AttributeError` in `handle` (L132) |

The server doesn't check arguments against its own `inputSchema`. Models often
send `null` for optional fields, so `limit: null` is a likely real-world
trigger.

### 3. Notifications other than `notifications/initialized` get an error response (observed)
`notifications/cancelled` returns `200` with
`{"jsonrpc":"2.0","id":null,"error":{"code":-32601,...}}`. Under the spec, a
notification never gets a JSON-RPC response; the server should reply
`202 Accepted` with no body. Clients send `notifications/cancelled` when a call
times out or the user interrupts, and `notifications/roots/list_changed` in
some setups. An error with `id: null` can be logged as a protocol error or
break the client's response matching. Fix: any message without an `id` should
get `202`.

### 4. `structuredContent` can violate the declared `outputSchema` (observed)
`add_note` accepted `{"title":"","body":""}`, even though `inputSchema` says
`title` has `minLength: 1`. A later `get_note` on that note returned
`structuredContent.title == ""`, but `get_note`'s `outputSchema` requires
`minLength: 1`. Clients that validate structured output against `outputSchema`
(the official TypeScript SDK does this) will reject the call. The note can then
never be read through `get_note`.

## Medium

### 5. Tool failures are sent as JSON-RPC protocol errors (L157-162)
- `get_note` on a missing id returns `error: {code: -32602, "note not found: n-99"}`
  **(observed)**.

The spec separates protocol errors from tool execution errors. A missing
record is an execution error and should come back as a result with
`isError: true`, so the model sees the message and can recover (for example,
by calling `search_notes`). Many clients show protocol errors to the user as a
failed call and never pass the text to the model.

Also, an unknown tool returns `-32601`. The spec's example for an unknown tool
uses `-32602`. This is minor.

### 6. Origin header isn't checked (DNS rebinding) (observed)
A request with `Origin: http://evil.example` was served normally. The
Streamable HTTP transport spec says servers MUST validate `Origin`. Reads need
no auth, so any web page the user visits could read the notes through DNS
rebinding to 127.0.0.1. Binding to localhost is good, but it doesn't prevent
this.

### 7. Race when generating `add_note` ids (L125-126)
`ThreadingHTTPServer` handles requests concurrently. `max(...)+1` and the dict
insert happen without a lock, so two concurrent `add_note` calls can get the
same id, and one note silently overwrites the other. The `NOTES` dict is also
read while another thread may be inserting into it.

### 8. Batch requests (L203-209) (observed)
JSON arrays are accepted and answered with `200 [...]`. JSON-RPC batching was
removed in protocol 2025-06-18, which is the version this server announces.
This doesn't break clients that don't batch, but it has gaps:
- Batched calls skip logging and session-id handling.
- A batch made only of notifications returns `200 []` instead of `202`.
- Any crash from item 2 inside a batch drops the whole batch.

## Low

9. **Version negotiation is ignored.** `initialize` always answers
   `2025-06-18`, whatever the client asks for (a `2025-03-26` request got
   `2025-06-18`, **observed**). The `MCP-Protocol-Version` header is never
   read. The spec allows this, but an older client that doesn't support
   2025-06-18 will disconnect instead of falling back.
10. **Sessions aren't real sessions.** A `Mcp-Session-Id` is issued at
    `initialize` but never stored or validated, and `DELETE` always returns
    `204`. Clients are fine with that, but the header promises state that
    doesn't exist.
11. **`search_notes.limit` isn't bounds-checked.** `limit: -1` silently drops
    the last hit (`hits[:-1]`, **observed**). `limit: 0` returns nothing.
12. **Snippets are cut from the wrong offset (L107-109).** The match index
    comes from `title + " " + body`, but the snippet is sliced from `body`. The
    result is shifted by `len(title)+1`, and a title-only match returns an
    unrelated or empty snippet (**observed**: query "o" on `n-3` gave a snippet
    that doesn't contain the match at its centre).
13. **Strict path matching.** `/mcp?x=1` returns 404 (**observed**). Some
    proxies and clients append query strings.
14. **No chunked request bodies.** Without `Content-Length`, the body is read
    as empty and treated as `{}`, so the reply is
    `method not found: None` with `id: null` (**observed**). Most clients send
    `Content-Length`, but any client that streams its request body will fail.
15. **HTTP/1.0 only.** `BaseHTTPRequestHandler` defaults to HTTP/1.0, so every
    request opens a new TCP connection. This works, but it's slower and
    sometimes surprises keep-alive pools.
16. **Built-in token.** The dev token `dev-token-123` is the default when
    `NOTES_TOKEN` is unset, and it's published in the README. The comparison
    isn't constant-time either.
17. **Notes are lost on restart.** `add_note` only writes to memory, so notes
    added by clients disappear when the server restarts.

## What worked fine
- `initialize`, `ping`, `tools/list`, `notifications/initialized` (202) and
  successful `search_notes` / `get_note` calls behave correctly.
- `structuredContent` is sent alongside a JSON text block.
- Malformed JSON gets a proper `-32700` parse error.
- `GET /mcp` returning 405 is allowed: the server simply offers no SSE stream.

## Suggested order of fixes
1. Stop using HTTP 401 for per-call authorization (item 1).
2. Add a catch-all around `handle()` that returns `-32603`, and validate
   arguments against `inputSchema` (items 2 and 4).
3. Return `202` for every notification (item 3).
4. Turn tool failures into `isError` results (item 5).
5. Add an Origin allow-list and a lock around writes (items 6 and 7).
