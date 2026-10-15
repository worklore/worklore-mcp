#!/usr/bin/env python3
"""Format check = the story's Verify adapted to CSV.
usage: grade_format.py <run_dir>   (reads <run_dir>/out/plan.csv and plan.md)"""
import csv, io, json, re, sys
from pathlib import Path

R = Path(sys.argv[1]); out = R / "out"
SQUARES = {
    "target_market": r"target\s*market|mercado\s*objetivo",
    "message": r"\bmessage\b|\bmensaje\b",
    "media": r"\bmedia\b|\bmedios?\b",
    "capture_leads": r"captur\w*\s*(the\s*)?leads?|lead\s*captur\w*",
    "nurture_leads": r"nurtur\w*\s*(the\s*)?leads?|lead\s*nurtur\w*",
    "sales_conversion": r"sales?\s*conversion|convert\w*\s*(to\s*)?sales?|conversi[oó]n",
    "world_class_experience": r"world[\s-]*class",
    "lifetime_value": r"lifetime\s*value|\bLTV\b",
    "referrals": r"referral",
}
PHASE_SQ = {"before": ["target_market", "message", "media"],
            "during": ["capture_leads", "nurture_leads", "sales_conversion"],
            "after": ["world_class_experience", "lifetime_value", "referrals"]}

def load_csv(p):
    raw = p.read_bytes().decode("utf-8-sig", errors="replace")
    rows = [[c.strip() for c in r] for r in csv.reader(io.StringIO(raw))]
    if max((len(r) for r in rows), default=0) <= 1:  # not comma-separated: sniff
        try:
            d = csv.Sniffer().sniff(raw[:4000], delimiters=";\t")
            rows = [[c.strip() for c in r] for r in csv.reader(io.StringIO(raw), d)]
        except Exception:
            pass
    return rows

res = {"csv_exists": (out / "plan.csv").exists(), "md_exists": (out / "plan.md").exists()}
rows = load_csv(out / "plan.csv") if res["csv_exists"] else []
md = (out / "plan.md").read_text(errors="replace") if res["md_exists"] else ""
flat = "\n".join(" | ".join(r) for r in rows)

# 1. title
tstrict = re.compile(r"1-Page Marketing Plan\s*[—–]\s*Taller Lento")
tlen = re.compile(r"1[\s-]*page\s+marketing\s+plan\s*[—–:\-|]\s*.*taller\s+lento", re.I)
res["title_strict_csv"] = bool(rows) and any(tstrict.search(c) for r in rows[:3] for c in r)
res["title_csv"] = bool(rows) and any(tlen.search(c) for r in rows[:3] for c in r)
res["title_md"] = bool(tlen.search("\n".join(md.splitlines()[:5])))

def heading(c):
    ls = [l.strip() for l in c.strip().split("\n") if l.strip()]
    return " / ".join(ls[:2])[:120]

# phases: a cell whose heading names the phase as a word
def phase_row(name):
    for i, r in enumerate(rows):
        for c in r:
            if re.search(rf"\b{name}\b", heading(c)[:40], re.I):
                return i
    return None
pr = {p: phase_row(p) for p in PHASE_SQ}
res["phases_csv"] = all(v is not None for v in pr.values())

# 3/4. nine named squares: the cell whose heading names the square earliest
def find(rx):
    best = None
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            m = re.search(rx, heading(c), re.I)
            if m and (best is None or m.start() < best[0]):
                best = (m.start(), i, j)
    return (best[1], best[2]) if best else None
sq = {}
for k, rx in SQUARES.items():
    pos = find(rx); filled = False
    if pos:
        i, j = pos; c = rows[i][j]
        rest = re.sub(rx, "", c, count=1, flags=re.I)
        cands = [rest]
        if j + 1 < len(rows[i]): cands.append(rows[i][j + 1])
        if i + 1 < len(rows) and j < len(rows[i + 1]): cands.append(rows[i + 1][j])
        filled = any(len(re.sub(r"[\W_\d]+", "", x)) >= 20 for x in cands)
    sq[k] = {"pos": pos, "filled": filled}

# head area = rows above the grid (first phase row or first square row)
first = min([v for v in pr.values() if v is not None] + [v["pos"][0] for v in sq.values() if v["pos"]], default=0)
head = "\n".join(" | ".join(r) for r in rows[:first])
# 2. assumptions (item + sale) stated in the CSV above the grid
res["assump_item_csv"] = bool(re.search(r"\bitem\b|what (we|I|is being) (sell|market)|product|offer(ing)?\b", head, re.I))
res["assump_sale_csv"] = bool(re.search(r"\bsale\b|conversion|counts as", head, re.I))
res["assump_item_md"] = bool(re.search(r"\bthe item\b|\bitem\b\s*[:\*]", md, re.I))
res["assump_sale_md"] = bool(re.search(r"the sale\b|\"the sale\"|“the sale”|\bsale\b\s*[:\*]|what counts as (a )?(sale|conversion)", md, re.I))
res["squares"] = sq
res["nine_named_filled"] = all(v["pos"] and v["filled"] for v in sq.values())
grid = True
for p, ks in PHASE_SQ.items():
    ps = [sq[k]["pos"] for k in ks]
    if not all(ps): grid = False; continue
    same_row = len({x[0] for x in ps}) == 1 and len({x[1] for x in ps}) == 3
    same_col = len({x[1] for x in ps}) == 1 and len({x[0] for x in ps}) == 3
    grid &= same_row or same_col
res["grid_3x3"] = grid
# shape-only: some 3x3 block of substantial (>=40 chars) cells
big = [[len(c) >= 40 for c in r] for r in rows]
res["grid_shape_3x3"] = sum(1 for r in big if sum(r[:3]) == 3) >= 3
res["csv_rows"] = len(rows); res["csv_max_cols"] = max((len(r) for r in rows), default=0)
items = {
    "title": res["title_csv"],
    "assumption_item": res["assump_item_csv"],
    "assumption_sale": res["assump_sale_csv"],
    "phases": res["phases_csv"],
    "nine_squares": res["nine_named_filled"],
}
res["items"] = items
res["format_pass"] = all(items.values()) and res["md_exists"]
print(json.dumps(res, indent=1, default=str))
