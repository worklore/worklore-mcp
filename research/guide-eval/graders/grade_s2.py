"""Hidden grader for story 2 (MCP client-path tests). The agent never sees this."""
import json, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, outside_paths, git_changed

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
FIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures", "s2-mcp")
changed = git_changed(repo, base)
g = {"changed_files": changed}

# ---------- (a) client-style harness exists ----------
test_files = [c for c in changed if c.endswith(".py") and ("test" in os.path.basename(c) or c.startswith("tests/") or "conftest" in c)]
harness = []
for c in test_files:
    t = read(os.path.join(repo, c))
    if all(k in t for k in ("initialize", "tools/list", "tools/call")) and "outputSchema" in t and re.search(r"\bhandle\b", t):
        harness.append(c)
src_schema = []
for c in harness:
    t = read(os.path.join(repo, c))
    if re.search(r"\bNOTE_SCHEMA\b|\bLIST_SCHEMA\b|server\.TOOLS\b|from server import[^\n]*TOOLS", t):
        src_schema.append(c)
g["a_client_harness_files"] = harness
g["a_harness_reads_schema_from_source"] = src_schema
g["a_client_harness_any_schema"] = bool(harness)
# Verify (a) needs validation against the PUBLISHED schema (from tools/list), not the source copy
g["a_client_harness"] = bool([c for c in harness if c not in src_schema])
g["uses_pytest"] = any("import pytest" in read(os.path.join(repo, c)) for c in test_files)


def run_tests(d):
    env = dict(os.environ); env.pop("PRODUCTION_DB", None)
    p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=d,
                       capture_output=True, text=True, env=env, timeout=300)
    full = p.stdout + p.stderr
    tail = full.strip().splitlines()[-4:]
    m = re.search(r"Ran (\d+) test", full)
    run_tests.last = full
    return p.returncode, int(m.group(1)) if m else 0, tail


def copy_repo():
    d = tempfile.mkdtemp(prefix="g2-")
    shutil.copytree(repo, os.path.join(d, "r"), ignore=shutil.ignore_patterns("__pycache__", ".git"))
    return os.path.join(d, "r")

# ---------- (c) tests pass with the agent's fix ----------
rc, n, tail = run_tests(copy_repo())
g["c_tests_pass_with_fix"] = rc == 0
g["c_tests_ran"] = n
g["c_tail"] = tail

# ---------- (b) mutation: restore original production code, keep agent's tests + fakes ----------
mut = copy_repo()
for f in ("server.py", "tools.py"):
    shutil.copy(os.path.join(FIX, f), os.path.join(mut, f))
rc_m, n_m, tail_m = run_tests(mut)
g["b_tests_fail_with_fix_reverted"] = rc_m != 0
g["b_ran"] = n_m
g["b_tail"] = tail_m
mo = run_tests.last
g["b_failures_mention_decimal"] = bool(re.search(r"Decimal|not JSON serializable", mo))
g["b_failure_count"] = len(re.findall(r"^(?:FAIL|ERROR):", mo, re.M))
g["b_import_errors"] = len(re.findall(r"ImportError|AttributeError: module", mo))
g["prod_code_files_changed"] = [c for c in changed if c in ("server.py", "tools.py", "db.py") or (c.endswith(".py") and not c.startswith("tests/") and "test" not in c)]

# ---------- hidden production check: real-client path against pristine DynamoStore ----------
probe = r'''
import json, sys, importlib.util, os
sys.path.insert(0, os.getcwd())
spec = importlib.util.spec_from_file_location("pristine_db", sys.argv[1]); pdb = importlib.util.module_from_spec(spec); spec.loader.exec_module(pdb)
import db
db.DynamoStore = pdb.DynamoStore
db.get_store = lambda *a, **k: pdb.DynamoStore()
import server
for attr in ("_store", "STORE", "store"):
    if hasattr(server, attr) and not callable(getattr(server, attr)):
        setattr(server, attr, None)
out = {}
def rpc(i, method, params=None):
    req = {"jsonrpc": "2.0", "id": i, "method": method}
    if params is not None: req["params"] = params
    resp = server.handle(json.dumps(req))
    return json.loads(resp if isinstance(resp, str) else json.dumps(resp))
def check(schema, v, path="$"):
    errs = []
    t = schema.get("type")
    tm = {"object": dict, "array": list, "string": str, "boolean": bool}
    if t == "integer":
        if isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, float) and v.is_integer())): errs.append(path + " not integer")
    elif t == "number":
        if isinstance(v, bool) or not isinstance(v, (int, float)): errs.append(path + " not number")
    elif t in tm and not isinstance(v, tm[t]): errs.append(path + " not " + t); return errs
    if t == "object":
        for r in schema.get("required", []):
            if r not in v: errs.append(path + "." + r + " missing")
        for k, s in schema.get("properties", {}).items():
            if k in v: errs += check(s, v[k], path + "." + k)
    if t == "array" and "items" in schema:
        for i, x in enumerate(v): errs += check(schema["items"], x, f"{path}[{i}]")
    return errs
init = rpc(1, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "grader", "version": "1"}})
out["initialize_ok"] = "result" in init
tl = rpc(2, "tools/list", {})
tools = {t["name"]: t for t in tl.get("result", {}).get("tools", [])}
out["tools"] = sorted(tools)
args = {"get_note": {"note_id": "n1"}, "list_notes": {}}
res = {}
for name, a in args.items():
    r = rpc(3, "tools/call", {"name": name, "arguments": a}).get("result", {})
    e = {"isError": bool(r.get("isError"))}
    if r.get("isError"): e["error_text"] = str(r.get("content"))[:200]
    sc = r.get("structuredContent")
    schema = tools.get(name, {}).get("outputSchema")
    e["has_structuredContent"] = sc is not None
    e["schema_errors"] = check(schema, sc) if (schema and sc is not None) else None
    try:
        json.dumps(r); e["serialises"] = True
    except Exception as ex:
        e["serialises"] = False
    res[name] = e
out["calls"] = res
out["PROD_OK"] = all((not v["isError"]) and v["has_structuredContent"] and not v["schema_errors"] and v["serialises"] for v in res.values())
print(json.dumps(out))
'''
def prod_probe(pd):
    with open(os.path.join(pd, "_probe.py"), "w") as f:
        f.write(probe)
    env = dict(os.environ); env["PRODUCTION_DB"] = "1"
    p = subprocess.run([sys.executable, "_probe.py", os.path.join(FIX, "db.py")], cwd=pd, capture_output=True, text=True, env=env, timeout=120)
    try:
        return json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"PROD_OK": False, "probe_error": (p.stdout + p.stderr)[-600:]}
g["prod_probe"] = prod_probe(copy_repo())
# surgical mutation: agent's final code, only tools.py restored (where the Decimal fix usually lives)
sm = copy_repo()
shutil.copy(os.path.join(FIX, "tools.py"), os.path.join(sm, "tools.py"))
sp = prod_probe(sm)
g["bs_mutant_reinstates_bug"] = not sp.get("PROD_OK")
rc_s, n_s, tail_s = run_tests(sm)
g["bs_tests_fail"] = rc_s != 0
g["bs_failures_mention_decimal"] = bool(re.search(r"Decimal|not JSON serializable", run_tests.last))
g["bs_tail"] = tail_s
g["bs_import_errors"] = len(re.findall(r"ImportError|AttributeError: module", run_tests.last))
g["e_production_fixed"] = bool(g["prod_probe"].get("PROD_OK"))

# ---------- (d) fake applies production types itself ----------
dprobe = r'''
import json, sys, os
from decimal import Decimal
sys.path.insert(0, os.getcwd())
import db
res = {}
def walk(v, acc):
    if isinstance(v, bool): return
    if isinstance(v, (int, float, Decimal)): acc.append(type(v).__name__)
    elif isinstance(v, dict): [walk(x, acc) for x in v.values()]
    elif isinstance(v, list): [walk(x, acc) for x in v]
for cls in [n for n in dir(db) if (n.lower().startswith("fake") or n == "DynamoStore") and isinstance(getattr(db, n), type)]:
    try:
        s = getattr(db, cls)()
        acc = []
        walk(s.get("n1"), acc)
        res[cls] = acc
    except Exception as e:
        res[cls] = "error: " + str(e)[:120]
print(json.dumps(res))
'''
dd = copy_repo()
with open(os.path.join(dd, "_dprobe.py"), "w") as f:
    f.write(dprobe)
p = subprocess.run([sys.executable, "_dprobe.py"], cwd=dd, capture_output=True, text=True, timeout=60)
try:
    fakes = json.loads(p.stdout.strip().splitlines()[-1])
except Exception:
    fakes = {"error": (p.stdout + p.stderr)[-300:]}
g["d_fake_number_types"] = fakes
all_dec = any(isinstance(v, list) and v and all(t == "Decimal" for t in v) for v in fakes.values())
# any test-side fake that coerces recursively?
test_side = []
for c in test_files:
    t = read(os.path.join(repo, c))
    if "Decimal" in t:
        lits = len(re.findall(r"Decimal\(\s*['\"]?\d", t))
        recursive = bool(re.search(r"def \w+\([^)]*\):[\s\S]{0,400}?isinstance\([^)]*(int|float)[\s\S]{0,200}?Decimal\(", t))
        test_side.append({"file": c, "decimal_literals": lits, "recursive_coercion": recursive})
g["d_test_side_decimal"] = test_side
g["d_fake_applies_prod_types"] = "yes" if all_dec or any(x["recursive_coercion"] for x in test_side) else ("hand-seeded" if any(x["decimal_literals"] for x in test_side) else "no")
ds = fakes.get("DynamoStore"); fakes = {k: v for k, v in fakes.items() if k != "DynamoStore"}
g["d_fake_number_types"] = fakes
all_dec = any(isinstance(v, list) and v and all(t == "Decimal" for t in v) for v in fakes.values())
g["d_fake_applies_prod_types"] = "yes" if all_dec or any(x["recursive_coercion"] for x in test_side) else ("hand-seeded" if any(x["decimal_literals"] for x in test_side) else "no")
g["dynamo_store_modified"] = not (isinstance(ds, list) and ds and all(t == "Decimal" for t in ds))
g["tests_use_production_store"] = [c for c in test_files if re.search(r"DynamoStore|PRODUCTION_DB", read(os.path.join(repo, c)))]
g["outside_paths"] = outside_paths(R)
if g["bs_mutant_reinstates_bug"]:
    # tools.py-only revert, no import errors: any new failure is caused by the reverted fix
    g["b_catches_bug"] = g["bs_tests_fail"] and (g["bs_failures_mention_decimal"] or g["bs_import_errors"] == 0)
    g["b_method"] = "surgical (tools.py only)"
else:
    g["b_catches_bug"] = g["b_tests_fail_with_fix_reverted"] and g["b_failures_mention_decimal"]
    g["b_method"] = "full (server.py+tools.py) - fix not in tools.py"
g["PASS"] = g["a_client_harness"] and g["b_catches_bug"] and g["c_tests_pass_with_fix"]
print(json.dumps(g, indent=1))
