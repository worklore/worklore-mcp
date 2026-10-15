#!/usr/bin/env python3
"""stdio MCP proxy: exposes worklore's hosted check_capability (same name, description, schema)
and forwards calls to https://worklore.dev/mcp anonymously. Logs every call's arguments to $PH_LOG.
Why: Claude Code 2.1.299 refuses to connect to the hosted server without OAuth, so every agent
goes through this proxy for a like-for-like test."""
import json, os, sys, urllib.request

URL = "https://worklore.dev/mcp"
LOG = os.environ.get("PH_LOG")


def upstream(method, params=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type": "application/json",
                                                          "accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


TOOLS = [t for t in upstream("tools/list")["result"]["tools"] if t["name"] == "check_capability"]

for line in sys.stdin:
    try:
        msg = json.loads(line)
    except Exception:
        continue
    mid, m = msg.get("id"), msg.get("method")
    if mid is None:
        continue
    if m == "initialize":
        res = {"protocolVersion": msg["params"].get("protocolVersion", "2025-06-18"),
               "capabilities": {"tools": {}}, "serverInfo": {"name": "worklore", "version": "proxy"}}
    elif m == "tools/list":
        res = {"tools": TOOLS}
    elif m == "tools/call":
        p = msg["params"]
        if LOG:
            with open(LOG, "a") as f:
                f.write(json.dumps({"name": p.get("name"), "arguments": p.get("arguments")}) + "\n")
        r = upstream("tools/call", p)
        res = r.get("result") or {"content": [{"type": "text", "text": json.dumps(r.get("error"))}], "isError": True}
    elif m == "ping":
        res = {}
    else:
        out = {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}
        print(json.dumps(out), flush=True)
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}), flush=True)
