"""n6: add the Hedera JavaScript SDK ("the current version from npm") and write src/transfer.ts, a signed 1 hbar
transfer printed as hex, offline.
Hidden answer key (a fact on no page the agent opens):
  The Hedera JS SDK moved to `@hiero-ledger/sdk` (2.90+, releases every few weeks). The old name `@hashgraph/sdk` is
  frozen at 2.81.0 (2026-03-13), is still `latest` on npm, is not marked deprecated, and its README is titled "Hiero
  JavaScript SDK" without saying the package moved. Every agent that decides from npm installs the old one, and the
  code works, so nothing tells it. (Round 11 screen source: worklore-research/2026-11-02-hedera-screen, 0 of 6 strong
  agents on the current SDK; rechecked on npm 2026-11-09.)
Behavioural check: the agent's script is run on two input sets it never saw (graders/n6_keys.txt: throwaway ED25519
  keys generated offline for this test, no account on any network), and each output is decoded and checked with the
  current SDK (graders/n6_verify/verify.mjs): transfers, memo, node, transaction ID and signature.
PASS = `@hiero-ledger/sdk` installed and the only SDK imported, `tsc --noEmit` clean, both outputs verify.
WORKS_ON_OLD_SDK = the same, but on `@hashgraph/sdk` (a working result on the legacy package; PASS false).
"""
import json, os, re, subprocess, sys

R = sys.argv[1]; W = os.path.join(R, "repo")
G = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PATH="/opt/homebrew/opt/node@24/bin:" + os.environ["PATH"])
KEYS = [l.split() for l in open(os.path.join(G, "n6_keys.txt")) if l.strip()]

def pkg_version(name):
    try: return json.load(open(os.path.join(W, "node_modules", name, "package.json")))["version"]
    except Exception: return None

# An agent may delete node_modules at the end to leave a clean tree (Codex did in n7, 2026-11-09): reinstall from its
# lockfile, so the run is graded on what it declared, not on whether it tidied up.
reinstalled = False
if not os.path.isdir(os.path.join(W, "node_modules")) and os.path.exists(os.path.join(W, "package-lock.json")):
    reinstalled = subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=W, capture_output=True,
                                 text=True, timeout=600, env=ENV).returncode == 0
g = {"answer_file": os.path.exists(os.path.join(W, "ANSWER.md")),
     "hiero_version": pkg_version("@hiero-ledger/sdk"), "hashgraph_version": pkg_version("@hashgraph/sdk")}
try:
    pj = json.load(open(os.path.join(W, "package.json")))
    g["package_json_sdk"] = {k: v for k, v in {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}.items()
                             if "sdk" in k or "hashgraph" in k or "hiero" in k}
except Exception:
    g["package_json_sdk"] = None
src = ""
for root, _, fs in os.walk(os.path.join(W, "src")):
    for fn in fs:
        if fn.endswith((".ts", ".js", ".mjs", ".cts", ".mts")): src += open(os.path.join(root, fn), errors="ignore").read()
g["imports_hiero"] = "@hiero-ledger/sdk" in src
g["imports_hashgraph"] = "@hashgraph/sdk" in src
g["on_current_sdk"] = bool(g["hiero_version"] and g["imports_hiero"] and not g["imports_hashgraph"])

if os.path.isdir(os.path.join(W, "node_modules")):
    r = subprocess.run(["npx", "--no-install", "tsc", "--noEmit", "-p", "."], cwd=W, capture_output=True, text=True,
                       timeout=300, env=ENV)
    g["tsc_ok"] = r.returncode == 0
    g["tsc_tail"] = (r.stdout + r.stderr)[-1200:]
else:
    g["tsc_ok"] = False; g["tsc_tail"] = "no node_modules"

cases = [("0.0.2001", KEYS[1], "0.0.2002", "1794000000"), ("0.0.48151", KEYS[2], "0.0.62342", "1795123456")]
g["cases"] = []
for op, (key, pub), rc, start in cases:
    e = dict(ENV, OPERATOR_ID=op, OPERATOR_KEY=key, RECIPIENT_ID=rc, VALID_START=start)
    try:
        p = subprocess.run(["npx", "--no-install", "tsx", "src/transfer.ts"], cwd=W, capture_output=True, text=True,
                           timeout=120, env=e)
        out = p.stdout.strip()
        hexes = re.findall(r"\b[0-9a-fA-F]{100,}\b", out)
        c = {"exit": p.returncode, "only_hex": bool(re.fullmatch(r"[0-9a-fA-F]+", out)), "err_tail": p.stderr[-300:]}
        if hexes:
            v = subprocess.run(["node", "verify.mjs", hexes[-1], op, rc, start, pub], cwd=os.path.join(G, "n6_verify"),
                               capture_output=True, text=True, timeout=60, env=ENV)
            c["verify"] = json.loads(v.stdout or "{}")
        else:
            c["verify"] = {"ok": False, "error": "no hex in output"}
    except subprocess.TimeoutExpired:
        c = {"exit": None, "verify": {"ok": False, "error": "timeout"}}
    g["cases"].append(c)
g["output_ok"] = all(c.get("exit") == 0 and c["verify"].get("ok") for c in g["cases"])
g["only_hex"] = all(c.get("only_hex") for c in g["cases"])

log = ""
for f in ("agent.log", "agent.err"):
    p = os.path.join(R, f)
    if os.path.exists(p): log += open(p, errors="ignore").read()
g["read_skill_md"] = "skill.md" in log
g["web_use"] = bool(re.search(r'"(WebFetch|WebSearch|web_search|google_web_search|web_fetch|read_url_content|search_web)"'
                              r'|docs\.hedera\.com', log))
g["npm_looked_up"] = sorted(set(re.findall(r"npm (?:view|info|show) (@[\w.-]+/sdk|hiero[\w-]*|@hashgraph/[\w-]+|@hiero-ledger/[\w-]+)", log)))
g["PASS"] = bool(g["on_current_sdk"] and g["tsc_ok"] and g["output_ok"])
g["WORKS_ON_OLD_SDK"] = bool(not g["on_current_sdk"] and g["hashgraph_version"] and g["tsc_ok"] and g["output_ok"])
g["reinstalled"] = reinstalled
print(json.dumps(g, indent=1))
