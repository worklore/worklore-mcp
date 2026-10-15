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


class _InvalidParams(Exception):
    pass


def _call_tool(name, arguments):
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise _InvalidParams("arguments must be an object")
    if name == "get_note":
        if not isinstance(arguments.get("note_id"), str):
            raise _InvalidParams("get_note requires a string 'note_id'")
    elif name == "list_notes":
        if arguments.get("tag") is not None and not isinstance(arguments["tag"], str):
            raise _InvalidParams("list_notes 'tag' must be a string")
    else:
        raise _InvalidParams(f"unknown tool: {name}")

    store = _get_store()
    try:
        if name == "get_note":
            data = tools.get_note(store, arguments["note_id"])
        else:
            data = tools.list_notes(store, arguments.get("tag"))
        text = json.dumps(data)
    except KeyError as exc:  # str(KeyError) adds stray quotes; use the message itself
        return _tool_error(exc.args[0] if exc.args else "not found")
    except Exception as exc:  # keep the server up; report the failure to the client
        return _tool_error(str(exc))
    return {"content": [{"type": "text", "text": text}], "structuredContent": data}


def _tool_error(message):
    return {"isError": True, "content": [{"type": "text", "text": str(message)}]}


def _error(rid, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}})


def handle(request_json):
    """Handle one JSON-RPC message. Returns the response string, or "" when the
    message was a notification (no reply; the HTTP layer should send 202 with no body)."""
    try:
        req = json.loads(request_json)
    except (ValueError, TypeError):
        return _error(None, -32700, "parse error")
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or not isinstance(req.get("method"), str):
        rid = req.get("id") if isinstance(req, dict) else None
        return _error(rid if isinstance(rid, (str, int)) else None, -32600, "invalid request")

    method = req["method"]
    if "id" not in req:
        return ""  # notification, e.g. notifications/initialized: never answered
    rid = req["id"]
    params = req.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return _error(rid, -32602, "params must be an object")

    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "notes-mcp", "version": "0.3.1"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        try:
            result = _call_tool(params.get("name"), params.get("arguments"))
        except _InvalidParams as exc:
            return _error(rid, -32602, str(exc))
    else:
        return _error(rid, -32601, f"method not found: {method}")
    return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})
