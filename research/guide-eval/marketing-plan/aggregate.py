#!/usr/bin/env python3
import json, re, statistics as st, itertools
from pathlib import Path
D = Path(__file__).resolve().parent
key = json.loads((D/"judging/key.json").read_text())
J = ["codex","gemini-pro","gemini-flash","claude-sonnet"]
VENDOR = {"codex":"openai","gemini-pro":"google","gemini-flash":"google","claude-sonnet":"anthropic"}
AV = {"codex":"openai","agy-pro":"google","agy-flash":"google","claude":"anthropic"}
scores = {}
for j in J:
    t = (D/f"judging/raw/{j}.txt").read_text()
    s = t[t.index("{"): t.rindex("}")+1]
    scores[j] = json.loads(s)["scores"]
C = ["C1","C2","C3","C4","C5"]
runs = {}
for pid, rid in key.items():
    a, arm = rid.rsplit("-",1)
    fmt = json.loads((D/f"runs/{rid}/format.json").read_text())
    meta = json.loads((D/f"runs/{rid}/meta.json").read_text())
    per = {j: {c: scores[j][pid][c]["score"] for c in C} | {"overall": scores[j][pid]["overall"]} for j in J}
    runs[rid] = {"pid": pid, "agent": a, "arm": arm, "wall_s": meta["wall_s"], "exit_code": meta["exit_code"],
                 "format_items": fmt["items"], "format_pass": fmt["format_pass"], "grid_3x3_named": fmt["grid_3x3"],
                 "title_strict_csv": fmt["title_strict_csv"], "title_md": fmt["title_md"],
                 "judges": per,
                 "mean": {c: round(st.mean(per[j][c] for j in J),2) for c in C+["overall"]},
                 "why": {j: {c: scores[j][pid][c]["why"] for c in C} | {"overall": scores[j][pid].get("overall_why","")} for j in J}}
# judge agreement: Spearman on overall across 8 plans
def rank(v):
    s = sorted(range(len(v)), key=lambda i: v[i]); r=[0]*len(v); i=0
    while i < len(s):
        k=i
        while k+1<len(s) and v[s[k+1]]==v[s[i]]: k+=1
        for m in range(i,k+1): r[s[m]]=(i+k)/2+1
        i=k+1
    return r
def spear(x,y):
    rx,ry=rank(x),rank(y); mx,my=st.mean(rx),st.mean(ry)
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry)); den=(sum((a-mx)**2 for a in rx)*sum((b-my)**2 for b in ry))**.5
    return round(num/den,2) if den else None
ids = sorted(runs)
agree = {f"{a}~{b}": spear([runs[r]["judges"][a]["overall"] for r in ids],[runs[r]["judges"][b]["overall"] for r in ids]) for a,b in itertools.combinations(J,2)}
# self-preference: judge's mean overall for own-vendor plans minus other judges' mean for those plans
selfp = {}
for j in J:
    own = [r for r in ids if AV[runs[r]["agent"]]==VENDOR[j]]
    if not own: continue
    mine = st.mean(runs[r]["judges"][j]["overall"] for r in own)
    others = st.mean(runs[r]["judges"][k]["overall"] for r in own for k in J if k!=j)
    mine_other = st.mean(runs[r]["judges"][j]["overall"] for r in ids if r not in own)
    oth_other = st.mean(runs[r]["judges"][k]["overall"] for r in ids if r not in own for k in J if k!=j)
    selfp[j] = {"own_vendor_plans": own, "judge_on_own": round(mine,2), "other_judges_on_own": round(others,2),
                "judge_on_rest": round(mine_other,2), "other_judges_on_rest": round(oth_other,2),
                "self_pref": round((mine-others)-(mine_other-oth_other),2)}
arm = {a: {c: round(st.mean(runs[r]["mean"][c] for r in ids if runs[r]["arm"]==a),2) for c in C+["overall"]} for a in ["without","with"]}
out = {"runs": runs, "judge_agreement_spearman_overall": agree, "self_preference": selfp, "arm_means": arm, "blind_key": key}
(D/"results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
# table
L = ["| agent | arm | format | title | item | sale | phases | 9 squares | C1 specific | C2 sale | C3 plain | C4 doable | C5 consistent | overall (mean) | codex | gemini-pro | gemini-flash | claude-sonnet | time |","|"+"---|"*19]
for a in ["claude","codex","agy-pro","agy-flash"]:
    for arm_ in ["without","with"]:
        r = runs[f"{a}-{arm_}"]; f=r["format_items"]; yn=lambda b:"Y" if b else "n"
        L.append(f"| {a} | {arm_} | {'**PASS**' if r['format_pass'] else 'fail'} | {yn(f['title'])} | {yn(f['assumption_item'])} | {yn(f['assumption_sale'])} | {yn(f['phases'])} | {yn(f['nine_squares'])} | "
                 + " | ".join(f"{r['mean'][c]:.2f}" for c in C) + f" | **{r['mean']['overall']:.2f}** | "
                 + " | ".join(str(r['judges'][j]['overall']) for j in J) + f" | {r['wall_s']}s |")
L.append(f"| **all** | without | | | | | | | " + " | ".join(f"{arm['without'][c]:.2f}" for c in C) + f" | **{arm['without']['overall']:.2f}** | | | | | |")
L.append(f"| **all** | with | | | | | | | " + " | ".join(f"{arm['with'][c]:.2f}" for c in C) + f" | **{arm['with']['overall']:.2f}** | | | | | |")
(D/"table.md").write_text("\n".join(L)+"\n")
print("\n".join(L)); print(json.dumps(agree)); print(json.dumps(selfp, indent=0))
# --- bias-adjusted views
R = out["runs"]; SM = {"codex":"codex","gemini-pro":"agy-pro","gemini-flash":"agy-flash"}
for r, v in R.items():
    v["overall_excl_same_vendor_judges"] = round(st.mean(v["judges"][j]["overall"] for j in J if VENDOR[j] != AV[v["agent"]]), 2)
out["arm_means_overall_excl_same_vendor"] = {a: round(st.mean(R[r]["overall_excl_same_vendor_judges"] for r in R if R[r]["arm"]==a), 2) for a in ["without","with"]}
out["same_model_self_preference"] = {f"{j} on {a}-{arm_}": {"judge": R[f"{a}-{arm_}"]["judges"][j]["overall"],
    "others_mean": round(st.mean(R[f"{a}-{arm_}"]["judges"][k]["overall"] for k in J if k != j), 2)}
    for j, a in SM.items() for arm_ in ["without","with"]}
(D/"results.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
