"""Minimal MCP server: JSON-RPC 2.0 over a single entry point."""
import json

import db
import tools

PROTOCOL_VERSION = "2025-06-18"

NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "word_count": {"type": "integer"},
        "stats": {
            "type": "object",
            "properties": {
                "views": {"type": "integer"},
                "rating": {"type": "number"},
                "revisions": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["views", "rating", "revisions"],
        },
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["id", "title", "word_count", "stats", "tags"],
}

LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "word_count": {"type": "integer"},
                },
                "required": ["id", "title", "word_count"],
            },
        },
        "count": {"type": "integer"},
    },
    "required": ["notes", "count"],
}

TOOLS = [
    {
        "name": "get_note",
        "description": "Fetch one note by id, with its stats.",
        "inputSchema": {
            "type": "object",
            "properties": {"note_id": {"type": "string"}},
            "required": ["note_id"],
        },
        "outputSchema": NOTE_SCHEMA,
    },
    {
        "name": "list_notes",
        "description": "List notes, optionally filtered by tag.",
        "inputSchema": {
            "type": "object",
            "properties": {"tag": {"type": "string"}},
        },
        "outputSchema": LIST_SCHEMA,
    },
]

_store = None


def _get_store():
    global _store
    if _store is None:
        _store = db.get_store()
    return _store


def _call_tool(name, arguments):
    store = _get_store()
    try:
        if name == "get_note":
            data = tools.get_note(store, arguments["note_id"])
        elif name == "list_notes":
            data = tools.list_notes(store, arguments.get("tag"))
        else:
            return {"isError": True, "content": [{"type": "text", "text": f"unknown tool {name}"}]}
        return {
            "content": [{"type": "text", "text": json.dumps(data)}],
            "structuredContent": data,
        }
    except Exception as exc:  # keep the server up; report the failure to the client
        return {"isError": True, "content": [{"type": "text", "text": str(exc)}]}


def handle(request_json):
    """Handle one JSON-RPC message. Returns the response string, or None for a
    notification (no "id"), which must not be answered -- send HTTP 202, no body."""
    try:
        req = json.loads(request_json)
    except ValueError:
        return json.dumps({"jsonrpc": "2.0", "id": None,
                           "error": {"code": -32700, "message": "parse error"}})
    if not isinstance(req, dict):
        return json.dumps({"jsonrpc": "2.0", "id": None,
                           "error": {"code": -32600, "message": "invalid request"}})
    method = req.get("method")
    if "id" not in req:
        return None
    rid = req.get("id")
    if method == "ping":
        result = {}
    elif method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "notes-mcp", "version": "0.3.1"},
        }
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = req.get("params", {})
        result = _call_tool(params.get("name"), params.get("arguments", {}))
    else:
        return json.dumps({"jsonrpc": "2.0", "id": rid,
                           "error": {"code": -32601, "message": f"method not found: {method}"}})
    return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})
