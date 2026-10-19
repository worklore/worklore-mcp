#!/usr/bin/env python3
"""notes-mcp: a small remote MCP server (Streamable HTTP, JSON responses).

    python3 server.py            # listens on http://127.0.0.1:52028/mcp
    PORT=9000 python3 server.py

Reads are open. Writes and the resources endpoints need
`Authorization: Bearer <token>`; the dev token is in TOKEN below.
"""
import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "52028"))
TOKEN = os.environ.get("NOTES_TOKEN", "dev-token-123")
PROTOCOL = "2025-06-18"
HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "notes.json")) as f:
    NOTES = {n["id"]: n for n in json.load(f)}

TOOLS = [
    {
        "name": "search_notes",
        "description": "Full-text search over the notes. Returns id, title and a snippet per hit.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 50}},
            "required": ["query"],
        },
        "outputSchema": {"type": "object"},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "get_note",
        "description": "One note in full by id (ids look like n-12).",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "pattern": "^n-[0-9]+$"}},
            "required": ["id"],
        },
        "outputSchema": {
            "type": "object",
            "required": ["id", "title", "body", "words"],
            "properties": {
                "id": {"type": "string", "pattern": "^n-[0-9]+$"},
                "title": {"type": "string", "minLength": 1},
                "body": {"type": "string"},
                "words": {"type": "integer", "minimum": 0},
                "tags": {"type": "array", "items": {"type": "string", "minLength": 1}},
            },
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "add_note",
        "description": "Create a note. Needs a signed-in session.",
        "inputSchema": {
            "type": "object",
            "properties": {"title": {"type": "string", "minLength": 1}, "body": {"type": "string"}},
            "required": ["title", "body"],
        },
        "outputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string", "pattern": "^n-[0-9]+$"}},
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False},
    },
]

RESOURCES = [
    {"uri": "notes://guide", "name": "guide", "mimeType": "text/markdown", "description": "How to use this server"},
]


def log(method, tool=None, ok=True, ms=0, who="anon"):
    rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "method": method, "tool": tool, "ok": ok, "ms": round(ms, 1), "who": who}
    sys.stderr.write(json.dumps(rec) + "\n")
    sys.stderr.flush()


def rpc_result(id_, result):
    return 200, {"jsonrpc": "2.0", "id": id_, "result": result}


def rpc_error(id_, code, message):
    return 200, {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def tool_result(text, structured=None, is_error=False):
    r = {"content": [{"type": "text", "text": text}], "isError": is_error}
    if structured is not None:
        r["structuredContent"] = structured
    return r


def call_tool(name, args, who):
    if name == "search_notes":
        q = str(args.get("query", "")).lower()
        limit = int(args.get("limit", 10))
        hits = []
        for n in NOTES.values():
            text = (n["title"] + " " + n["body"]).lower()
            if q in text:
                i = text.find(q)
                hits.append({"id": n["id"], "title": n["title"], "snippet": n["body"][max(0, i - 30): i + 50]})
        hits = hits[:limit]
        return tool_result(json.dumps(hits), {"hits": hits, "total": len(hits)})
    if name == "get_note":
        nid = args.get("id")
        if nid is None:
            raise ValueError("missing required argument: id")
        n = NOTES.get(nid)
        if n is None:
            raise ValueError(f"note not found: {nid}")
        out = {"id": n["id"], "title": n["title"], "body": n["body"], "words": len(n["body"].split()), "tags": n.get("tags", [])}
        return tool_result(json.dumps(out), out)
    if name == "add_note":
        if who == "anon":
            return None  # caller turns this into a 401
        nid = f"n-{max(int(k[2:]) for k in NOTES) + 1}"
        NOTES[nid] = {"id": nid, "title": args["title"], "body": args["body"], "tags": []}
        return tool_result(json.dumps({"id": nid}), {"id": nid})
    return None


def handle(req, who):
    method = req.get("method")
    id_ = req.get("id")
    params = req.get("params") or {}
    if method == "initialize":
        return rpc_result(id_, {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}},
            "serverInfo": {"name": "notes-mcp", "version": "0.3.1"},
            "instructions": "Search and read notes. add_note needs a signed-in session.",
        })
    if method == "notifications/initialized":
        return 202, None
    if method == "ping":
        return rpc_result(id_, {})
    if method == "tools/list":
        return rpc_result(id_, {"tools": TOOLS})
    if method in ("resources/list", "resources/read", "resources/templates/list"):
        if who == "anon":
            return 401, {"error": "unauthorized"}
        if method == "resources/list":
            return rpc_result(id_, {"resources": RESOURCES})
        if method == "resources/templates/list":
            return rpc_result(id_, {"resourceTemplates": []})
        return rpc_result(id_, {"contents": [{"uri": "notes://guide", "mimeType": "text/markdown", "text": "# notes-mcp\nsearch_notes, get_note, add_note."}]})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if not any(t["name"] == name for t in TOOLS):
            return rpc_error(id_, -32601, f"unknown tool: {name}")
        try:
            res = call_tool(name, args, who)
        except ValueError as e:
            return rpc_error(id_, -32602, str(e))
        if res is None:
            return 401, {"error": "sign in required"}
        return rpc_result(id_, res)
    return rpc_error(id_, -32601, f"method not found: {method}")


class Handler(BaseHTTPRequestHandler):
    server_version = "notes-mcp/0.3.1"

    def _send(self, status, body, session=None):
        data = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        if data:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if session:
            self.send_header("Mcp-Session-Id", session)
        self.end_headers()
        if data:
            self.wfile.write(data)

    def do_GET(self):
        self._send(405, {"error": "use POST"})

    def do_DELETE(self):
        self._send(204, None)

    def do_POST(self):
        if self.path.rstrip("/") != "/mcp":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        try:
            req = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}})
        auth = self.headers.get("Authorization", "")
        who = "dev" if auth == f"Bearer {TOKEN}" else "anon"
        session = self.headers.get("Mcp-Session-Id")
        t0 = time.time()
        if isinstance(req, list):
            out = []
            for r in req:
                _, b = handle(r, who)
                if b is not None:
                    out.append(b)
            return self._send(200, out, session)
        status, body = handle(req, who)
        if req.get("method") == "initialize" and not session:
            session = uuid.uuid4().hex
        ok = status < 400 and not (isinstance(body, dict) and "error" in body)
        log(req.get("method"), (req.get("params") or {}).get("name"), ok, (time.time() - t0) * 1000, who)
        self._send(status, body, session)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    sys.stderr.write(f"notes-mcp listening on http://127.0.0.1:{PORT}/mcp\n")
    sys.stderr.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
