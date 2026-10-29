#!/usr/bin/env python3
"""Round 8 tables from runs/*/grade.json + meta.json -> stdout (markdown).
Five repetitions per cell: a cell shows passes/runs; story and agent totals pool the repetitions."""
import glob, json, os, re, collections
H = os.path.dirname(os.path.abspath(__file__))
AG = ["claude-opus", "claude-sonnet", "claude-haiku", "codex-sol", "codex-sol-low", "agy-flash-low", "agy-oss"]
ARMS = ["none-en", "example-en", "none-ru", "example-ru", "example-ruru"]
STORIES = ["s1", "s3", "s7", "s10", "s8", "s11"]
STORY = {"s1": "HR corridors (fact not in the docs)", "s3": "silent launchd job (two bugs, one silent)",
         "s7": "Intervals OAuth quirks (fact on a forum)", "s10": "event per keystroke (trap)",
         "s8": "two cache_control segments (control: fact in docs)", "s11": "crash on the second write (control: derivable)"}
runs = collections.defaultdict(list)   # (story, agent, arm) -> [(meta, grade, cyr_share)]
for d in sorted(glob.glob(os.path.join(H, "runs", "*"))):
    try:
        m = json.load(open(os.path.join(d, "meta.json"))); g = json.load(open(os.path.join(d, "grade.json")))
    except Exception as e:
        print(f"<!-- {os.path.basename(d)}: {e} -->"); continue
    if m.get("rep", 1) < 1 or m.get("limit"): continue
    ans = ""
    try: ans = open(os.path.join(d, "repo", "ANSWER.md"), encoding="utf-8", errors="ignore").read()
    except Exception: pass
    letters = re.findall(r"[A-Za-zА-Яа-яЁё]", ans)
    cyr = sum(1 for c in letters if re.match(r"[А-Яа-яЁё]", c)) / len(letters) if letters else None
    runs[(m["story"], m["agent"], m["arm"])].append((m, g, cyr))

def passes(rs):
    ok = [bool(g.get("PASS")) and m["exit_code"] == 0 for m, g, _ in rs]
    return sum(ok), len(ok)
def frac(k, n): return f"{k}/{n}" if n else "·"

print("# Round 8 tables\n")
print("## Passes per story and arm (five repetitions × seven agents = 35 runs per cell when complete)\n")
print("| story | " + " | ".join(ARMS) + " | gain en | gain ru | gain ru (ru story) |")
print("|---|" + "---|" * (len(ARMS) + 3))
tot = {arm: [0, 0] for arm in ARMS}
for s in STORIES:
    row = {}
    for arm in ARMS:
        rs = [r for a in AG for r in runs.get((s, a, arm), [])]
        row[arm] = passes(rs); tot[arm][0] += row[arm][0]; tot[arm][1] += row[arm][1]
    def gain(a, b):
        (ka, na), (kb, nb) = row[a], row[b]
        return f"{(kb/nb - ka/na)*100:+.0f} pp" if na and nb else "·"
    print(f"| {s} {STORY[s]} | " + " | ".join(frac(*row[arm]) for arm in ARMS)
          + f" | {gain('none-en', 'example-en')} | {gain('none-ru', 'example-ru')} | {gain('none-ru', 'example-ruru')} |")
print("| **all** | " + " | ".join(f"**{frac(*tot[arm])}**" for arm in ARMS) + " | | | |\n")

print("## Passes per agent and arm (six stories × five repetitions = 30 runs per cell when complete)\n")
print("| agent | " + " | ".join(ARMS) + " |"); print("|---|" + "---|" * len(ARMS))
for a in AG:
    print(f"| {a} | " + " | ".join(frac(*passes([r for s in STORIES for r in runs.get((s, a, arm), [])])) for arm in ARMS) + " |")
print()

print("## Per cell: passes out of the repetitions run (the heatmap)\n")
for s in STORIES:
    print(f"### {s}: {STORY[s]}\n")
    print("| agent | " + " | ".join(ARMS) + " | mean s per arm |"); print("|---|" + "---|" * (len(ARMS) + 1))
    for a in AG:
        cells, times = [], []
        for arm in ARMS:
            rs = runs.get((s, a, arm), [])
            k, n = passes(rs); cells.append(frac(k, n))
            times.append(str(round(sum(m["wall_s"] for m, _, _ in rs) / len(rs))) if rs else "·")
        print(f"| {a} | " + " | ".join(cells) + " | " + "/".join(times) + " |")
    print()

print("## Answer language: share of Cyrillic letters in ANSWER.md, mean per agent and arm\n")
print("| agent | " + " | ".join(ARMS) + " |"); print("|---|" + "---|" * len(ARMS))
for a in AG:
    row = []
    for arm in ARMS:
        xs = [c for s in STORIES for _, _, c in runs.get((s, a, arm), []) if c is not None]
        row.append(f"{sum(xs)/len(xs):.0%}" if xs else "·")
    print(f"| {a} | " + " | ".join(row) + " |")
print()

import random
random.seed(8)
def pool(arm, stories=STORIES, agents=AG):
    return [bool(g.get("PASS")) and m["exit_code"] == 0 for s in stories for a in agents for m, g, _ in runs.get((s, a, arm), [])]
def rate(xs): return sum(xs) / len(xs) if xs else float("nan")
def boot(f, pools, n=4000):
    """95% CI of f(resampled pools) by bootstrap over runs within each pool."""
    vals = []
    for _ in range(n):
        vals.append(f(*[[random.choice(p_) for _ in p_] for p_ in pools]))
    vals.sort(); return vals[int(0.025 * n)], vals[int(0.975 * n)]
def pp(x): return f"{x*100:+.0f} pp"
print("## The question, with intervals (bootstrap over runs, 95%)\n")
print("| contrast | stories | estimate | 95% CI |\n|---|---|---|---|")
for label, stories in (("all six", STORIES), ("the four where the story mattered", ["s1", "s3", "s7", "s10"]), ("the two controls", ["s8", "s11"])):
    P = {arm: pool(arm, stories) for arm in ARMS}
    rows = [
        ("task in Russian, no story: none-ru − none-en", lambda a, b: rate(b) - rate(a), [P["none-en"], P["none-ru"]]),
        ("story gain in English: example-en − none-en", lambda a, b: rate(b) - rate(a), [P["none-en"], P["example-en"]]),
        ("story gain in Russian: example-ru − none-ru", lambda a, b: rate(b) - rate(a), [P["none-ru"], P["example-ru"]]),
        ("difference of differences: gain ru − gain en", lambda a, b, c, d: (rate(d) - rate(c)) - (rate(b) - rate(a)), [P["none-en"], P["example-en"], P["none-ru"], P["example-ru"]]),
        ("translated story: example-ruru − example-ru", lambda a, b: rate(b) - rate(a), [P["example-ru"], P["example-ruru"]]),
        ("Russian task with the English story vs English task with it: example-ru − example-en", lambda a, b: rate(b) - rate(a), [P["example-en"], P["example-ru"]]),
    ]
    for name, f, pools in rows:
        lo, hi = boot(f, pools)
        print(f"| {name} | {label} | {pp(f(*pools))} | {pp(lo)} to {pp(hi)} |")
print()

print("## Task language per agent: passes without a story, English vs Russian task (30 runs each when complete)\n")
print("| agent | none-en | none-ru | Δ | example-en | example-ru | example-ruru |\n|---|---|---|---|---|---|---|")
for a in AG:
    P = {arm: pool(arm, STORIES, [a]) for arm in ARMS}
    d = rate(P["none-ru"]) - rate(P["none-en"]) if P["none-en"] and P["none-ru"] else float("nan")
    print(f"| {a} | {sum(P['none-en'])}/{len(P['none-en'])} | {sum(P['none-ru'])}/{len(P['none-ru'])} | {pp(d)} | "
          + " | ".join(f"{sum(P[x])}/{len(P[x])}" for x in ("example-en", "example-ru", "example-ruru")) + " |")
print()

WEB = {"claude": r'"name":"(?:WebSearch|WebFetch)"', "codex": r'(?m)^.*"item\.completed".*"type":"web_search".*$', "agy": r'"tool_name":"(?:search_web|read_url_content|browser_[a-z_]+)"'}
def web_calls(m):
    h = "claude" if m["agent"].startswith("claude") else "codex" if m["agent"].startswith("codex") else "agy"
    try: txt = open(os.path.join(H, "runs", m["id"], "agent.log"), errors="ignore").read()
    except OSError: return 0
    return len(re.findall(WEB[h], txt))
print("## Web use: runs with at least one web search or fetch (and the number of calls), per agent and arm\n")
print("Counted from the harness logs: Claude Code `WebSearch`/`WebFetch` tool calls, Codex `web_search` events, Antigravity `search_web`/`read_url_content` calls.\n")
print("| agent | " + " | ".join(ARMS) + " |"); print("|---|" + "---|" * len(ARMS))
for a in AG:
    row = []
    for arm in ARMS:
        cs = [web_calls(m) for s in STORIES for m, _, _ in runs.get((s, a, arm), [])]
        row.append(f"{sum(1 for c in cs if c)}/{len(cs)} ({sum(cs)})" if cs else "·")
    print(f"| {a} | " + " | ".join(row) + " |")
print()
print("### Web use per story, all agents: runs with a web call / runs\n")
print("| story | " + " | ".join(ARMS) + " |"); print("|---|" + "---|" * len(ARMS))
for s in STORIES:
    row = []
    for arm in ARMS:
        cs = [web_calls(m) for a in AG for m, _, _ in runs.get((s, a, arm), [])]
        row.append(f"{sum(1 for c in cs if c)}/{len(cs)}" if cs else "·")
    print(f"| {s} | " + " | ".join(row) + " |")
print()

print("## Wall time: mean seconds per run, per arm\n")
print("| agent | " + " | ".join(ARMS) + " |"); print("|---|" + "---|" * len(ARMS))
for a in AG + ["all"]:
    row = []
    for arm in ARMS:
        ts = [m["wall_s"] for s in STORIES for ag in (AG if a == "all" else [a]) for m, _, _ in runs.get((s, ag, arm), [])]
        row.append(str(round(sum(ts) / len(ts))) if ts else "·")
    print(f"| {a} | " + " | ".join(row) + " |")
print()

print("## Runs that are not results\n")
bad = [(k, m) for k, rs in runs.items() for m, g, _ in rs if m["exit_code"] != 0]
if not bad: print("none\n")
for (s, a, arm), m in bad:
    print(f"- {m['id']}: exit {m['exit_code']} ({'timeout' if m['exit_code'] == 124 else 'error'}), {m['wall_s']} s")
print()
