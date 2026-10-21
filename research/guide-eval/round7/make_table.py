#!/usr/bin/env python3
"""Round 7 tables from runs/*/grade.json + meta.json -> stdout (markdown)."""
import glob, json, os
H = os.path.dirname(os.path.abspath(__file__))
AG = ["claude-opus", "claude-sonnet", "claude-haiku", "codex-sol", "codex-sol-low", "agy-flash-low", "agy-oss"]
ARMS = ["none", "follow", "example", "notes"]
STORIES = ["s7", "s8", "s9", "s10", "s11", "s12"]
STORY = {"s7": "Intervals OAuth quirks (niche fact)", "s8": "two cache_control segments (fact in docs)", "s9": "DynamoDB reserved words (two bugs, one silent)",
         "s10": "PostHog event per keystroke (trap to fall into)", "s11": "crash on the second write (derivable)", "s12": "two-account authorization test (method)"}
runs = {}
for d in sorted(glob.glob(os.path.join(H, "runs", "*"))):
    try:
        m = json.load(open(os.path.join(d, "meta.json"))); g = json.load(open(os.path.join(d, "grade.json")))
    except Exception as e:
        print(f"<!-- {os.path.basename(d)}: {e} -->"); continue
    runs[(m["story"], m["agent"], m["arm"])] = (m, g)
def cell(s, a, arm):
    r = runs.get((s, a, arm))
    if not r: return "·"
    m, g = r
    if m["exit_code"] == 3: return "q"
    if m["exit_code"] == 124: return "t"
    if m["exit_code"] != 0: return f"err{m['exit_code']}"
    return "**P**" if g.get("PASS") else "f"
print("## PASS grid (P = pass, f = fail, t = timeout at 20 min (fail), q = quota exhausted (not run), · = not run)\n")
for s in STORIES:
    print(f"### {s}: {STORY[s]}\n")
    print("| agent | " + " | ".join(ARMS) + " | time none/follow/example/notes |")
    print("|---|" + "---|" * (len(ARMS) + 1))
    for a in AG:
        times = "/".join(str(runs[(s, a, arm)][0]["wall_s"]) if (s, a, arm) in runs else "·" for arm in ARMS)
        print(f"| {a} | " + " | ".join(cell(s, a, arm) for arm in ARMS) + f" | {times} |")
    print()
def totals(title, keyf, keys):
    print(f"## {title}\n")
    print("| | " + " | ".join(ARMS) + " |"); print("|---|" + "---|" * len(ARMS))
    for k in keys:
        row = []
        for arm in ARMS:
            xs = [g.get("PASS") for (ss, aa, ar), (m, g) in runs.items() if keyf(ss, aa) == k and ar == arm and m["exit_code"] != 3]
            row.append(f"{sum(bool(x) for x in xs)}/{len(xs)}" if xs else "·")
        print(f"| {k} {STORY.get(k, '')} | " + " | ".join(row) + " |")
    print()
totals("Totals per story and arm (passes / runs)", lambda s, a: s, STORIES)
totals("Totals per agent and arm", lambda s, a: a, AG)
print("## Detail per run (every boolean or list field of the grade, in the grader's order)\n")
for s in STORIES:
    rs = [(a, arm) for a in AG for arm in ARMS if (s, a, arm) in runs]
    if not rs: continue
    cols = [k for k, v in runs[(s,) + rs[0]][1].items() if k != "PASS" and (isinstance(v, bool) or isinstance(v, list))][:12]
    print(f"### {s}\n"); print("| agent | arm | PASS | " + " | ".join(cols) + " | chars | s |"); print("|---|---|---|" + "---|" * (len(cols) + 2))
    for a, arm in rs:
        m, g = runs[(s, a, arm)]
        def fmt(v):
            if isinstance(v, bool): return "Y" if v else "n"
            if isinstance(v, list): return str(len(v)) if v else "-"
            return str(v)
        print(f"| {a} | {arm} | {'P' if g.get('PASS') else 'f'} | " + " | ".join(fmt(g.get(c)) for c in cols) + f" | {g.get('answer_chars', '')} | {m['wall_s']} |")
    print()
