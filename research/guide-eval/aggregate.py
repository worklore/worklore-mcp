import json, os, glob
D = os.path.dirname(os.path.abspath(__file__))
rows = []
for R in sorted(glob.glob(os.path.join(D, "runs", "*"))):
    try:
        meta = json.load(open(os.path.join(R, "meta.json")))
    except Exception:
        continue
    try:
        g = json.load(open(os.path.join(R, "grade.json")))
    except Exception as e:
        g = {"grader_error": str(e)}
    for k in ("changed_files", "c_tail", "b_tail"):
        g.pop(k, None)
    notes_p = os.path.join(R, "notes.txt")
    meta["notes"] = open(notes_p).read().strip() if os.path.exists(notes_p) else ""
    meta["grade"] = g
    rows.append(meta)
json.dump(rows, open(os.path.join(D, "results.json"), "w"), indent=1)
print(len(rows), "runs")
for r in rows:
    g = r["grade"]
    print(r["id"], r["exit_code"], r["wall_s"], "PASS" if g.get("PASS") else "fail")
