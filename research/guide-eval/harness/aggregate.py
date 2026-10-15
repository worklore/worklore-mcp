import json, os, glob, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
def J(p):
    try: return json.load(open(p))
    except Exception: return None
rows = []
for R in sorted(glob.glob(os.path.join(D, "runs", "*"))):
    m = J(os.path.join(R, "meta.json"))
    if not m: continue
    b = json.loads(subprocess.run([sys.executable, os.path.join(D, "behave.py"), R], capture_output=True, text=True).stdout or "{}")
    json.dump(b, open(os.path.join(R, "behave.json"), "w"), indent=1, ensure_ascii=False)
    g = J(os.path.join(R, "grade.json")) or {}
    go = J(os.path.join(R, "grade_old.json"))
    for k in ("changed_files",): g.pop(k, None)
    if go: go.pop("changed_files", None)
    n = os.path.join(R, "notes.txt")
    m.update(grade=g, grade_old_verify=go, behaviour=b, notes=open(n).read().strip() if os.path.exists(n) else "")
    rows.append(m)
json.dump(rows, open(os.path.join(D, "results.json"), "w"), indent=1, ensure_ascii=False)
print(len(rows), "runs")
