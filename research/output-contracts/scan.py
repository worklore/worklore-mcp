#!/usr/bin/env python3
"""Anonymous, read-only checkup of public MCP servers from the official registry.

Only questions anyone may ask without a token: initialize, notifications/initialized,
tools/list, resources/list / prompts/list (only when advertised), and one extra
initialize with protocolVersion "banana". NEVER tools/call: annotations can lie,
and a call can cost the owner money or change something.

A few requests per server, servers in parallel but never two at once on the same
host, 15 s timeouts, a User-Agent that points to the checkup story.

Usage: python3 scan.py sample N   -> registry sample (remote URL + repo) to sample.json
       python3 scan.py run        -> results.jsonl (resumable)
       python3 scan.py report     -> report.md
"""
import concurrent.futures as cf, json, os, re, sys, threading, time, urllib.error, urllib.parse, urllib.request

HERE = os.environ.get("SCAN_OUT") or os.path.dirname(os.path.abspath(__file__))
UA = "worklore-mcp-checkup/0.1 (read-only; https://worklore.dev/s/2026-10-06-check-your-mcp-server-in-a-few-minutes-the-failures-real-cli)"
NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
REG = "https://registry.modelcontextprotocol.io/v0/servers?limit=50"

def get_json(url):
    for i in range(4):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30))
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError("registry unavailable")

def sample(n):
    out, cur, seen = [], None, set()
    while len(out) < n:
        d = get_json(REG + ("&cursor=" + urllib.parse.quote(cur) if cur else ""))
        for s in d.get("servers", []):
            x = s.get("server", s)
            if not (s.get("_meta") or {}).get("io.modelcontextprotocol.registry/official", {}).get("isLatest"):
                continue
            repo = (x.get("repository") or {}).get("url") or ""
            for r in x.get("remotes") or []:
                url = r.get("url") or ""
                if r.get("type") != "streamable-http" or "{" in url or not url.startswith("https://") or not repo:
                    continue
                host = urllib.parse.urlparse(url).netloc
                if host in seen or host.endswith("worklore.dev"):
                    continue
                seen.add(host)
                out.append({"name": x.get("name"), "version": x.get("version"), "url": url, "repo": repo,
                            "website": x.get("websiteUrl") or ""})
                break
        cur = (d.get("metadata") or {}).get("nextCursor")
        if not cur:
            break
    json.dump(out[:n], open(os.path.join(HERE, "sample.json"), "w"), indent=1)
    print(f"sampled {len(out[:n])}")

def sample_random(n, seed=20261006):
    """Crawl the WHOLE registry (no page cap), then draw n at random: the
    registry lists alphabetically, so the first pages are not a fair sample."""
    import random
    pool, cur, seen = [], None, set()
    while True:
        d = get_json(REG + ("&cursor=" + urllib.parse.quote(cur) if cur else ""))
        for s in d.get("servers", []):
            x = s.get("server", s)
            if not (s.get("_meta") or {}).get("io.modelcontextprotocol.registry/official", {}).get("isLatest"):
                continue
            for r in x.get("remotes") or []:
                url = r.get("url") or ""
                if r.get("type") != "streamable-http" or "{" in url or not url.startswith("https://"):
                    continue
                host = urllib.parse.urlparse(url).netloc
                if host in seen or host.endswith("worklore.dev"):
                    continue
                seen.add(host)
                pool.append({"name": x.get("name"), "version": x.get("version"), "url": url,
                             "repo": (x.get("repository") or {}).get("url") or "", "website": x.get("websiteUrl") or ""})
                break
        cur = (d.get("metadata") or {}).get("nextCursor")
        if not cur:
            break
    random.Random(seed).shuffle(pool)
    json.dump(pool[:n], open(os.path.join(HERE, "sample.json"), "w"), indent=1)
    print(f"pool {len(pool)} distinct remote hosts; sampled {min(n, len(pool))}")

def rpc(url, method, params=None, sid=None, notify=False):
    body = {"jsonrpc": "2.0", "method": method}
    if not notify:
        body["id"] = 1
    if params is not None:
        body["params"] = params
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
         "User-Agent": UA, "MCP-Protocol-Version": "2025-06-18"}
    if sid:
        h["Mcp-Session-Id"] = sid
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=15)
        status, hdrs, raw = r.status, r.headers, r.read(2_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status, hdrs, raw = e.code, e.headers, e.read(200_000).decode("utf-8", "replace")
    except Exception as e:
        return {"status": None, "error": type(e).__name__ + ": " + str(e)[:160]}
    msg = None
    if "text/event-stream" in (hdrs.get("Content-Type") or ""):
        for line in raw.splitlines():
            if line.startswith("data:"):
                try:
                    m = json.loads(line[5:].strip())
                    if isinstance(m, dict) and ("result" in m or "error" in m):
                        msg = m
                except json.JSONDecodeError:
                    pass
    else:
        try:
            msg = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            msg = None
    return {"status": status, "msg": msg, "sid": hdrs.get("Mcp-Session-Id"),
            "www": hdrs.get("WWW-Authenticate"), "raw": None if msg else raw[:200]}

INIT = {"protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "worklore-mcp-checkup", "version": "0.1"}}

def check(s):
    url, r = s["url"], {"server": s, "checks": {}, "facts": {}}
    c, f = r["checks"], r["facts"]
    init = rpc(url, "initialize", INIT)
    f["init_status"] = init.get("status")
    res = (init.get("msg") or {}).get("result") if isinstance(init.get("msg"), dict) else None
    if init.get("status") in (401, 403):
        f["closed"] = True                     # an observation, never a failure
        return r
    if not res:
        f["unreachable"] = init.get("error") or f"HTTP {init.get('status')} {init.get('raw') or ''}"[:200]
        return r
    sid = init.get("sid")
    f["protocol"] = res.get("protocolVersion")
    f["server_version"] = (res.get("serverInfo") or {}).get("version")
    f["server_name"] = (res.get("serverInfo") or {}).get("name")
    caps = res.get("capabilities") or {}
    f["caps"] = sorted(caps)
    rpc(url, "notifications/initialized", None, sid, notify=True)

    # C6: the registry listing describes the server that answers
    if f["server_version"] and s.get("version") and f["server_version"] != s["version"]:
        c["version_drift"] = f"registry lists {s['version']}, server reports {f['server_version']}"

    # C1/C8: tool list and names
    tl = rpc(url, "tools/list", {}, sid)
    f["tools_status"] = tl.get("status")
    tres = (tl.get("msg") or {}).get("result") if isinstance(tl.get("msg"), dict) else None
    if tl.get("status") in (401, 403):
        f["tools_closed"] = True
        if "tools" in caps:
            c["advertised_but_401"] = c.get("advertised_but_401", []) + ["tools/list"]
    elif tres is not None:
        tools = tres.get("tools") or []
        f["tool_count"] = len(tools)
        bad = [t.get("name") for t in tools if not NAME_RE.match(str(t.get("name", "")))]
        if bad:
            c["bad_tool_names"] = bad[:10]
        f["no_annotations"] = sum(1 for t in tools if not (t.get("annotations") or {}))

    # advertised capabilities that refuse anonymous callers right after an anonymous initialize
    for cap, m in (("resources", "resources/list"), ("prompts", "prompts/list")):
        if cap in caps:
            x = rpc(url, m, {}, sid)
            if x.get("status") in (401, 403):
                c["advertised_but_401"] = c.get("advertised_but_401", []) + [m]

    # C9: honest version negotiation
    b = rpc(url, "initialize", dict(INIT, protocolVersion="banana"))
    bres = (b.get("msg") or {}).get("result") if isinstance(b.get("msg"), dict) else None
    if bres and bres.get("protocolVersion") == "banana":
        c["echoes_banana"] = True
    return r

def run():
    sample_ = json.load(open(os.path.join(HERE, "sample.json")))
    path = os.path.join(HERE, "results.jsonl")
    done = set()
    if os.path.exists(path):
        done = {json.loads(l)["server"]["url"] for l in open(path)}
    todo = [s for s in sample_ if s["url"] not in done]
    lock = threading.Lock()
    with cf.ThreadPoolExecutor(8) as ex, open(path, "a") as out:
        for r in ex.map(check, todo):
            with lock:
                out.write(json.dumps(r) + "\n"); out.flush()
    print(f"checked {len(todo)} (total {len(done) + len(todo)})")

def report():
    rows = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl"))]
    n = len(rows)
    closed = [r for r in rows if r["facts"].get("closed")]
    unreach = [r for r in rows if r["facts"].get("unreachable")]
    open_ = [r for r in rows if not r["facts"].get("closed") and not r["facts"].get("unreachable")]
    kinds = ["version_drift", "bad_tool_names", "advertised_but_401", "echoes_banana"]
    L = [f"# MCP checkup sample — {time.strftime('%Y-%m-%d')}", "",
         f"Servers checked: {n} · answered initialize anonymously: {len(open_)} · "
         f"closed at initialize (401/403, an observation): {len(closed)} · unreachable/broken: {len(unreach)}", ""]
    for k in kinds:
        L.append(f"- {k}: {sum(1 for r in open_ if k in r['checks'])} of {len(open_)}")
    tl = [r for r in open_ if "tool_count" in r["facts"]]
    L.append(f"- tools/list answered anonymously: {len(tl)} · of those, tools with no annotations at all: "
             f"{sum(r['facts']['no_annotations'] for r in tl)} of {sum(r['facts']['tool_count'] for r in tl)}")
    L += ["", "## Candidates (at least one unambiguous failure)", "",
          "| server | repo | findings |", "|---|---|---|"]
    for r in open_:
        if r["checks"]:
            L.append(f"| {r['server']['name']} | {r['server']['repo']} | "
                     + "; ".join(f"{k}: {v}" for k, v in r["checks"].items()).replace("|", "/") + " |")
    open(os.path.join(HERE, "report.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:12]))

if __name__ == "__main__":
    {"sample": lambda: sample(int(sys.argv[2])), "random": lambda: sample_random(int(sys.argv[2])), "run": run, "report": report}[sys.argv[1]]()
