#!/usr/bin/env python3
"""stdio MCP proxy for guide-eval round 9. Exposes the tools worklore's hosted server answers
anonymously (name, description and schema taken from its tools/list), forwards every call unchanged
and anonymously to https://worklore.dev/mcp, and appends one line per call to $PH_LOG:
{"ts", "name", "arguments", "ok", "error", "result_chars"}.
Copied from research/2026-10-14-paste-hash/proxy.py (which exposed check_capability only) and
extended to the whole anonymous set. Stdlib only."""
import json, os, sys, time, urllib.request, urllib.error

URL = os.environ.get("WL_MCP_URL", "https://worklore.dev/mcp")
LOG = os.environ.get("PH_LOG")
ANON = ("search_stories", "get_story", "suggest_for_project", "check_capability", "explore_keywords")


def parse_body(raw):
    """The server answers JSON; tolerate an SSE body (data: lines) as well."""
    txt = raw.decode("utf-8", errors="replace")
    try:
        return json.loads(txt)
    except ValueError:
        last = None
        for line in txt.splitlines():
            if line.startswith("data:"):
                try:
                    last = json.loads(line[5:].strip())
                except ValueError:
                    pass
        if last is None:
            raise
        return last


def upstream(method, params=None):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"content-type": "application/json",
                                                          "accept": "application/json, text/event-stream",
                                                          "user-agent": "guide-eval-round9-proxy/1.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return parse_body(r.read())


def log(rec):
    if not LOG:
        return
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


TOOLS = None
for attempt in range(3):
    try:
        TOOLS = [t for t in upstream("tools/list")["result"]["tools"] if t["name"] in ANON]
        break
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"proxy: tools/list failed ({e}), retry {attempt + 1}\n")
        time.sleep(2)
if not TOOLS:
    sys.stderr.write("proxy: could not fetch tools/list from upstream, exiting\n")
    sys.exit(1)

for line in sys.stdin:
    try:
        msg = json.loads(line)
    except Exception:  # noqa: BLE001
        continue
    mid, m = msg.get("id"), msg.get("method")
    if mid is None:           # notifications (notifications/initialized, cancelled): nothing to answer
        continue
    if m == "initialize":
        res = {"protocolVersion": (msg.get("params") or {}).get("protocolVersion", "2025-06-18"),
               "capabilities": {"tools": {}}, "serverInfo": {"name": "worklore", "version": "proxy-r9"}}
    elif m == "tools/list":
        res = {"tools": TOOLS}
    elif m == "tools/call":
        p = msg.get("params") or {}
        rec = {"ts": round(time.time(), 3), "name": p.get("name"), "arguments": p.get("arguments")}
        try:
            r = upstream("tools/call", p)
            res = r.get("result") or {"content": [{"type": "text", "text": json.dumps(r.get("error"))}], "isError": True}
            rec["ok"] = not res.get("isError", False)
            rec["error"] = None if rec["ok"] else json.dumps(r.get("error"))[:200]
        except Exception as e:  # noqa: BLE001
            res = {"content": [{"type": "text", "text": f"upstream error: {e}"}], "isError": True}
            rec["ok"] = False; rec["error"] = str(e)[:200]
        rec["result_chars"] = len(json.dumps(res))
        log(rec)
    elif m == "ping":
        res = {}
    else:
        print(json.dumps({"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "method not found"}}), flush=True)
        continue
    print(json.dumps({"jsonrpc": "2.0", "id": mid, "result": res}), flush=True)
