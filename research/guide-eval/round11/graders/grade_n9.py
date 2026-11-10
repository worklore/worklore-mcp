#!/usr/bin/env python3
"""n9: rewrite a 6-line fetch CLI with Effect, "the current version from npm" (Effect 4.x; 4.1.2 on 2026-11-09).
Hidden answer key (a fact newer than the models): Effect 4.0 (2026-10-01) renamed much of the v3 API the models
  learned: Context.Tag -> Context.Service, HTTP moved from @effect/platform into effect/http, Schema reworked
  (Schema.TaggedError, Config.String; v3-style Schema.TaggedErrorClass / Config.string don't exist). @effect/platform
  on npm is still the v3-era 0.97.2 and not deprecated. The `effect` package ships AGENTS.md, CLAUDE.md and ai-docs/
  (runnable examples, including an HttpClient service with retryTransient) in node_modules/effect.
Behavioural check: the agent's repo (R/repo, node_modules included, as the run left it) is type-checked and its CLI is
  run against a local fake rates service in five scenarios (ok; 503 twice then ok, expects 3 requests; unknown
  currency; invalid body; always 503, expects 4 requests and exit 3). Never reads the agent's answer.
PASS = effect 4.x installed, `tsc --noEmit` clean, all five scenarios right.
Ported from ~/projects/worklore-research/2026-11-02-effect4-screen/grade.py (argv: R; node from the default PATH, the
  same node the agent had).
"""

import http.server, json, os, re, subprocess, sys, threading
from collections import Counter

R = sys.argv[1]; W = os.path.join(R, "repo")
ENV = dict(os.environ)
GOOD = {"base": "USD", "date": "2026-11-02", "rates": {"EUR": 0.92141, "GBP": 0.78}}
hits = Counter()

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        mode = self.path.split("/")[1]
        hits[mode] += 1
        if mode == "flaky" and hits[mode] <= 2 or mode == "down":
            return self.send(503, {"error": "busy"})
        if mode == "bad":
            return self.send(200, {"base": "USD", "date": "2026-11-02", "rates": {"EUR": "0.92"}})
        if self.path.rstrip("/").endswith("/rates/USD"):
            return self.send(200, GOOD)
        return self.send(404, {"error": "not found"})
    def send(self, code, body):
        b = json.dumps(body).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]

def pkg_version(name):
    try: return json.load(open(os.path.join(W, "node_modules", name, "package.json")))["version"]
    except Exception: return None

# An agent may delete node_modules at the end to leave a clean tree (Codex did in n7, 2026-11-09): reinstall from its
# lockfile, so the run is graded on what it declared, not on whether it tidied up.
reinstalled = False
if not os.path.isdir(os.path.join(W, "node_modules")) and os.path.exists(os.path.join(W, "package-lock.json")):
    reinstalled = subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=W, capture_output=True,
                                 text=True, timeout=600, env=ENV).returncode == 0
g = {"effect_version": pkg_version("effect"), "platform_version": pkg_version("@effect/platform"),
     "platform_node_version": pkg_version("@effect/platform-node"), "schema_pkg_version": pkg_version("@effect/schema")}
try:
    pj = json.load(open(os.path.join(W, "package.json")))
    g["package_json_effect"] = {k: v for k, v in {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}.items() if "effect" in k}
except Exception:
    g["package_json_effect"] = None
g["on_effect_4"] = bool(g["effect_version"] and g["effect_version"].split(".")[0] == "4")

r = subprocess.run(["npx", "tsc", "--noEmit", "-p", "."], cwd=W, capture_output=True, text=True, timeout=300, env=ENV)
g["tsc_ok"] = r.returncode == 0
g["tsc_errors"] = len(re.findall(r"error TS\d+", r.stdout + r.stderr))
g["tsc_tail"] = (r.stdout + r.stderr)[-1500:]

def run(mode, args):
    hits[mode] = 0
    e = dict(ENV, RATES_URL=f"http://127.0.0.1:{port}/{mode}")
    try:
        p = subprocess.run(["npx", "tsx", "src/main.ts", *args], cwd=W, capture_output=True, text=True, timeout=60, env=e)
        return {"exit": p.returncode, "out": p.stdout[-300:], "err": p.stderr[-300:], "requests": hits[mode]}
    except subprocess.TimeoutExpired:
        return {"exit": None, "out": "", "err": "timeout", "requests": hits[mode]}

t = {}
o = run("ok", ["USD", "EUR"]);       t["ok"] = o["exit"] == 0 and "1 USD = 0.9214 EUR" in o["out"]
f = run("flaky", ["USD", "EUR"]);    t["retries_then_ok"] = f["exit"] == 0 and "1 USD = 0.9214 EUR" in f["out"] and f["requests"] == 3
u = run("ok", ["USD", "XYZ"]);       t["unknown_currency"] = u["exit"] == 1 and "unknown currency: XYZ" in u["err"]
b = run("bad", ["USD", "EUR"]);      t["invalid_response"] = b["exit"] == 2 and "invalid response" in b["err"]
d = run("down", ["USD", "EUR"]);     t["gives_up_after_3_retries"] = d["exit"] == 3 and d["requests"] == 4
g["tests"], g["runs"] = t, {"ok": o, "flaky": f, "unknown": u, "bad": b, "down": d}
g["tests_passed"] = sum(t.values())

src = ""
for root, _, fs in os.walk(os.path.join(W, "src")):
    for fn in fs:
        if fn.endswith(".ts"): src += open(os.path.join(root, fn), errors="ignore").read()
g["uses"] = {
    "effect_http": bool(re.search(r'from\s+"effect/http"', src)),
    "platform_pkg": "@effect/platform\"" in src or "@effect/platform'" in src or bool(re.search(r'from\s+["\']@effect/platform["/]', src)),
    "context_service": "Context.Service" in src, "context_tag": "Context.Tag" in src or "Context.GenericTag" in src,
    "effect_service": "Effect.Service" in src, "schema": "Schema." in src, "fetch_direct": bool(re.search(r'\bfetch\(', src)),
}
log = open(os.path.join(R, "agent.log"), errors="ignore").read() if os.path.exists(os.path.join(R, "agent.log")) else ""
g["read_shipped_docs"] = bool(re.search(r"node_modules/effect/(AGENTS|CLAUDE)\.md|node_modules/effect/ai-docs", log))
g["read_source"] = "node_modules/effect/src" in log or "node_modules/effect/dist" in log
g["web_use"] = bool(re.search(r'"(WebFetch|WebSearch|web_search|google_web_search|web_fetch|read_url_content)"|effect\.website', log))

g["PASS"] = bool(g["on_effect_4"] and g["tsc_ok"] and all(t.values()))
srv.shutdown()
g["reinstalled"] = reinstalled
print(json.dumps(g, indent=1))
