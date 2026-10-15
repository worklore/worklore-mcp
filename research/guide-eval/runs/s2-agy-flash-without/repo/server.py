"""Minimal MCP server: JSON-RPC 2.0 over a single entry point."""
import json
import os

import db
import tools

PROTOCOL_VERSION = "2025-06-18"
SUPPORTED_PROTOCOL_VERSIONS = {"2024-11-05", "2025-03-26", "2025-06-18"}

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
    is_prod = os.environ.get("PRODUCTION_DB") == "1"
    if _store is None or (is_prod != isinstance(_store, db.DynamoStore)):
        _store = db.get_store()
    return _store


def _call_tool(name, arguments):
    if arguments is None:
        arguments = {}
    elif not isinstance(arguments, dict):
        return {"isError": True, "content": [{"type": "text", "text": "arguments must be an object"}]}

    store = _get_store()
    try:
        if name == "get_note":
            if "note_id" not in arguments:
                return {"isError": True, "content": [{"type": "text", "text": "missing required argument 'note_id'"}]}
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
    try:
        req = json.loads(request_json)
    except Exception:
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Parse error"},
        })

    if not isinstance(req, dict):
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32600, "message": "Invalid Request: expected a JSON object"},
        })

    is_notification = "id" not in req
    rid = req.get("id")

    if req.get("jsonrpc") != "2.0":
        if is_notification:
            return ""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": rid if isinstance(rid, (str, int)) else None,
            "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"},
        })

    method = req.get("method")
    if not isinstance(method, str):
        if is_notification:
            return ""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": rid if isinstance(rid, (str, int)) else None,
            "error": {"code": -32600, "message": "Invalid Request: method must be a string"},
        })

    params = req.get("params")
    if params is None:
        params = {}
    elif not isinstance(params, dict):
        if is_notification:
            return ""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": rid,
            "error": {"code": -32602, "message": "Invalid params: params must be an object"},
        })

    if method == "initialize":
        client_version = params.get("protocolVersion")
        negotiated_version = (
            client_version if client_version in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
        )
        result = {
            "protocolVersion": negotiated_version,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "notes-mcp", "version": "0.3.1"},
        }
    elif method == "notifications/initialized" or method.startswith("notifications/"):
        if is_notification:
            return ""
        return json.dumps({"jsonrpc": "2.0", "id": rid, "result": {}})
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        result = _call_tool(params.get("name"), params.get("arguments"))
    else:
        if is_notification:
            return ""
        return json.dumps({
            "jsonrpc": "2.0",
            "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        })

    if is_notification:
        return ""
    return json.dumps({"jsonrpc": "2.0", "id": rid, "result": result})
