#!/usr/bin/env python3
"""Check that growing the pool to 100 tools left every N <= 50 exposure (names AND definitions) and GROUPED unchanged.
exposure-hashes-n50.json was recorded from the 50-tool server right before the extension."""
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
sys.exit(1 if bad else 0)
