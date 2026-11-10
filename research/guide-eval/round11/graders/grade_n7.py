"""n7: upgrade a small React + TS app from Pollar 0.10 to the current SDK (0.12), before sdk-api v1 retires.
Hidden answer key (from the 2026-11-06 Pollar screen, ~/projects/worklore-research/2026-11-06-pollar-screen):
  The upgrade breaks four things `tsc` reports (balance `string | null`, KycStatus 'expired', setTrustline's removed
  `sponsored` option, getRampsQuote gone -> quoteRamp) and two it doesn't:
  trap 1 (base_url): src/pollar.ts pins `baseUrl: 'https://sdk.api.pollar.xyz/v1'`. 0.12 appends the version itself,
    so baseUrl must be the origin (or removed); a pinned /v1 or /v2 typechecks and keeps the app on the retired API.
  trap 2 (balances): `balance` is now null when the chain could not be read. The quick tsc fix (`?? '0'`, a cast)
    shows a zero balance; the app must show no number (a dash or "unavailable").
  The quoteRamp rewrite must keep the meaning: pesos in, ARS per USDC out (amountIn / amountOut), null with no quote.
Behavioural check: graders/n7_check.ts imports the agent's modules with fake Pollar clients (no network).
PASS = @pollar/core and @pollar/react installed at 0.12+ and allowed by package.json, `tsc --noEmit` passes, and all
five runtime checks hold (base_url, balances, kyc, trustline, ramp).
"""
import json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, answer

R = sys.argv[1]; W = os.path.join(R, "repo")
G = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PATH="/opt/homebrew/opt/node@24/bin:" + os.environ["PATH"])

def installed(name):
    try: return json.load(open(os.path.join(W, "node_modules", name, "package.json")))["version"]
    except Exception: return None

def minor(v):
    m = re.match(r"(\d+)\.(\d+)", v or ""); return (int(m[1]), int(m[2])) if m else None

# An agent may delete node_modules at the end to leave a clean tree (Codex did, 2026-11-09): reinstall from its
# lockfile, so the run is graded on what it declared, not on whether it tidied up.
reinstalled = False
if not os.path.isdir(os.path.join(W, "node_modules")) and os.path.exists(os.path.join(W, "package-lock.json")):
    reinstalled = subprocess.run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=W, capture_output=True,
                                 text=True, timeout=600, env=ENV).returncode == 0
g = {"core_version": installed("@pollar/core"), "react_version": installed("@pollar/react"), "reinstalled": reinstalled}
try:
    pj = json.load(open(os.path.join(W, "package.json")))
    g["package_json_pollar"] = {k: v for k, v in {**pj.get("dependencies", {}), **pj.get("devDependencies", {})}.items() if k.startswith("@pollar/")}
except Exception:
    g["package_json_pollar"] = None
g["versions_ok"] = all((minor(g[k]) or (0, 0)) >= (0, 12) for k in ("core_version", "react_version")) \
    and bool(g["package_json_pollar"]) and not any(re.search(r"0\.(?:[0-9]|1[01])\b", v) and not re.search(r"0\.1[2-9]|latest|\*", v) for v in g["package_json_pollar"].values())

src = ""
for root, _, fs in os.walk(os.path.join(W, "src")):
    for fn in fs:
        if fn.endswith((".ts", ".tsx")): src += read(os.path.join(root, fn))
g["old_ramp_api_left"] = bool(re.search(r"getRampsQuote|createOnRamp|getRampCountries", src))

if os.path.isdir(os.path.join(W, "node_modules")):
    r = subprocess.run(["npx", "--no-install", "tsc", "--noEmit", "-p", "."], cwd=W, capture_output=True, text=True, timeout=300, env=ENV)
    g["tsc_ok"] = r.returncode == 0; g["tsc_tail"] = (r.stdout + r.stderr)[-1200:]
else:
    g["tsc_ok"] = False; g["tsc_tail"] = "no node_modules"

chk = os.path.join(W, "__check.ts"); c = None
shutil.copy(os.path.join(G, "n7_check.ts"), chk)
try:
    c = subprocess.run(["npx", "-y", "tsx", "__check.ts"], cwd=W, capture_output=True, text=True, timeout=180, env=ENV)
    g["checks"] = json.loads(c.stdout.strip().splitlines()[-1])
except Exception as e:
    g["checks"] = {"error": str(e)[:300], "stderr": (c.stderr if c else "")[-600:]}
finally:
    os.remove(chk)
for k in ("base_url", "balances", "kyc", "trustline", "ramp"):
    g[k + "_ok"] = bool(isinstance(g["checks"].get(k), dict) and g["checks"][k].get("ok"))
g["trap_base_url_ok"] = g["base_url_ok"]; g["trap_balance_ok"] = g["balances_ok"]

log = read(os.path.join(R, "agent.log"))
g["read_upgrade_guide"] = bool(re.search(r"UPGRADE\.md|upgrade-to-sdk-0-12|Upgrade to SDK 0\.12|api-versions", log))
g["read_llms_full"] = "llms-full.txt" in log
g["used_migrate_tool"] = "@pollar/migrate" in log
g["web_use"] = bool(re.search(r'"(WebFetch|WebSearch|web_search|search_web|web_fetch|read_url_content)"|docs\.pollar\.xyz', log))
g["answer_chars"] = len(answer(R) or "")
g["PASS"] = bool(g["versions_ok"] and g["tsc_ok"] and all(g[k + "_ok"] for k in ("base_url", "balances", "kyc", "trustline", "ramp")))
print(json.dumps(g, indent=1))
