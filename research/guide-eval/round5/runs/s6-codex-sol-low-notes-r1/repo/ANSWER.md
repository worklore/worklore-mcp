# MCP client compatibility review

I inspected `server.py` and probed a locally started `python3 server.py` at `/mcp`. The server file was not changed.

## Findings

1. **Malformed tool calls can close the HTTP connection with no response.** `tools/call` accepts arguments without validating them against the advertised `inputSchema` (`server.py:156-164`). With the development token, calling `add_note` with `{}` raises an uncaught `KeyError` at line 126; my probe received `RemoteDisconnected`. A noninteger `search_notes.limit` similarly raises uncaught `TypeError` or `ValueError`. Clients need a valid JSON-RPC error or tool error, not a dropped connection.

2. **HTTP sessions are advertised but not actually managed.** Initialization sends a new `Mcp-Session-Id` (`server.py:213-217`), yet later requests neither require nor validate it. A `ping` carrying `Mcp-Session-Id: bogus` succeeded and echoed `bogus`. `DELETE` returns 204 on any path without ending a session (`server.py:189-190`). A client that follows the session lifecycle cannot tell when a session is invalid or terminated. Either implement session tracking and the expected unknown-session response, or omit session IDs entirely.

3. **Resource reads ignore the requested URI.** `resources/read` always returns `notes://guide` (`server.py:148-155`). My request for `notes://missing` succeeded with guide content. Clients can display the wrong resource under the requested URI; unknown URIs should return an error.

4. **The advertised tool contracts are not enforced.** `get_note` accepts malformed IDs despite its pattern; `search_notes` accepts an empty/missing query and out-of-range limits; `add_note` accepts missing or wrongly typed fields until it crashes or stores them (`server.py:101-127`). This makes `tools/list` unreliable for clients that use its schemas to build calls. Validate argument objects and return consistent errors for invalid calls.

5. **Authentication cannot be discovered through the usual HTTP challenge.** Anonymous `resources/list` and `add_note` calls return bare HTTP 401 JSON objects (`server.py:148-150,165-167`), with no `WWW-Authenticate` header or authorization metadata. Clients that expect remote MCP OAuth discovery have no way to learn how to authenticate. If the fixed bearer token is intentional for local development, document that clients must be configured with the token in advance; for general remote clients, implement the MCP authorization flow.

6. **The transport accepts invalid JSON-RPC shapes without a reliable error.** `do_POST` never checks `jsonrpc`, `method`, ID type, or the shapes of `params` and batch elements (`server.py:192-217`). For example, an empty JSON object is treated as an unknown method, while a non-object JSON value or malformed batch element can raise an exception and drop the connection. Real clients may surface these as transport failures instead of actionable protocol errors.

7. **Concurrent writes can reuse note IDs.** `ThreadingHTTPServer` handles requests concurrently, but `add_note` computes `max(NOTES) + 1` and inserts without a lock (`server.py:123-127,224`). Two simultaneous writes can return the same ID and overwrite a note. The shared in-memory notes also disappear on restart, despite successful create responses.

## Probe details

The local probe used ordinary HTTP POST requests with JSON bodies. `initialize` returned HTTP 200 and a session ID; `ping` with a bogus session ID returned HTTP 200 and echoed it; authenticated `add_note` with empty arguments closed the connection; authenticated `resources/read` for a missing URI returned the guide; `DELETE /anything` returned HTTP 204. These outcomes match the code paths above.
