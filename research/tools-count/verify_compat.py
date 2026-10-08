#!/usr/bin/env python3
"""Check that growing the pool to 100 tools left every N <= 50 exposure (names AND definitions) and GROUPED unchanged.
exposure-hashes-n50.json was recorded from the 50-tool server right before the extension.

Also checks, for the vague-names variant (TC_NAMES=vague):
- default exposures are byte-identical on the wire: the exact bytes of initialize + tools/list for every task x
  N in 5..50, 75, 100 and GROUPED match exposure-hashes-wire.json, recorded before TC_NAMES existed;
- TC_NAMES=vague exposes the same tools in the same order with identical descriptions and schemas, only the names
  differ; the names are unique, valid MCP names and none is an honest name; calls map back to the honest op."""
import hashlib, json, os, sys
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import server as s
ref = json.load(open(os.path.join(H, "exposure-hashes-n50.json")))
tasks = json.load(open(os.path.join(H, "tasks.json")))["tasks"]
dig = lambda v: hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()
bad = []
for t in tasks:
    need = ",".join(sorted({x["tool"] for x in t["expected"]}))
    for n in range(5, 55, 5):
        names = s.exposed_tools(str(n), None, need=need)
        if dig({"names": names, "defs": s.tool_defs(str(n), names)}) != ref[f"{t['id']}|{n}"]:
            bad.append((t["id"], n))
    for n in (75, 100):
        names = s.exposed_tools(str(n), None, need=need)
        assert len(set(names)) == n and names[:50] == s.exposed_tools("50", None, need=need)
if dig(s.tool_defs("GROUPED", s.exposed_tools("GROUPED", None))) != ref["GROUPED"]:
    bad.append(("GROUPED", 7))
print("OK: all N<=50 exposures and GROUPED identical; N=75/100 extend N=50" if not bad else f"MISMATCH: {bad}")

import re, subprocess, tempfile
REQ = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18"}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n'
env0 = {k: v for k, v in os.environ.items() if not k.startswith("TC_")}
def wire(v, need, **extra):
    return subprocess.run([sys.executable, os.path.join(H, "server.py")], input=(REQ + extra.pop("more", "")).encode(),
                          capture_output=True, env=dict(env0, TC_VARIANT=v, TC_NEED=need, **extra)).stdout
wref = json.load(open(os.path.join(H, "exposure-hashes-wire.json")))
vn = s.vague_names(); assert set(vn) == set(s.POOL)
vals = list(vn.values())
assert len(set(vals)) == len(vals) and all(re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", x) for x in vals) and not set(vals) & set(s.POOL)
wbad, vbad = [], []
for t in tasks:
    need = ",".join(sorted({x["tool"] for x in t["expected"]}))
    for v in [str(n) for n in range(5, 55, 5)] + ["75", "100", "GROUPED"]:
        b = wire(v, need)
        if hashlib.sha256(b).hexdigest() != wref[f"{t['id']}|{v}"]: wbad.append((t["id"], v))
        if v in ("50", "100", "GROUPED"):
            h = [json.loads(l) for l in b.decode().splitlines()][1]["result"]["tools"]
            first = vn[h[0]["name"]] if v != "GROUPED" else h[0]["name"]
            with tempfile.NamedTemporaryFile(suffix=".jsonl") as lg:
                call = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": first, "arguments": {}}}) + "\n"
                g = [json.loads(l) for l in wire(v, need, TC_NAMES="vague", TC_LOG=lg.name, more=call).decode().splitlines()][1]["result"]["tools"]
                logged = [json.loads(l) for l in open(lg.name)]
            if v == "GROUPED":
                if g != h: vbad.append((t["id"], v, "grouped changed"))
                continue
            if [x["name"] for x in g] != [vn[x["name"]] for x in h] or [{**x, "name": 0} for x in g] != [{**x, "name": 0} for x in h]:
                vbad.append((t["id"], v, "defs"))
            if logged[-1].get("op") != h[0]["name"] or logged[-1].get("tool") != first or logged[0].get("names") != "vague":
                vbad.append((t["id"], v, "call mapping"))
print("OK: default initialize+tools/list bytes identical for all 234 task x size exposures (5-100, GROUPED)" if not wbad else f"WIRE MISMATCH: {wbad}")
print("OK: TC_NAMES=vague = same tools, order, descriptions, schemas; only names differ; calls map back to the honest op" if not vbad else f"VAGUE MISMATCH: {vbad}")
sys.exit(1 if bad or wbad or vbad else 0)
