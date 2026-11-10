#!/usr/bin/env python3
"""Round 11 tables: python3 make_table.py > table.md
A cell is passes/runs (PASS and exit code 0, runs marked "limit" excluded). Five repetitions: 30 runs per agent and arm.
Since the 2026-11-09 amendment (plan.md): stories n4, n6, n10 (new, unpublished, kept by screen.md) and the controls
s8, s11; the references claude-opus (none) and agy-oss (none, story) run in this round on n4, n6, n10."""
import collections, glob, json, os, random, re

H = os.path.dirname(os.path.abspath(__file__))
AG = ["claude-haiku", "codex-sol-low", "codex-oss", "vibe-devstral", "kimi-k31"]
REF = ["claude-opus", "agy-oss"]
OPEN = ["codex-oss", "vibe-devstral"]
ARMS = ["none", "story", "ticket"]
STORIES = ["n4", "n6", "n10", "s8", "s11"]
MATTER = ["n4", "n6", "n10"]                # the three new stories the screen kept
STORY = {"n4": "Codex -o under a sandbox: empty answer, exit 0 (trap)", "n6": "Hedera SDK moved to @hiero-ledger/sdk (fact not on npm)",
         "n10": "Prisma 8 has no @prisma/client (fact not on npm)",
         "s8": "two cache_control segments (control: fact in docs)", "s11": "crash on the second write (control: derivable)"}
PRICE = {"codex-oss": (0.15, 0.60)}         # OpenRouter $ per million input / output tokens, 2026-11-09

def load(folder, arm_map=None):
    runs = collections.defaultdict(list)
    for d in sorted(glob.glob(os.path.join(folder, "runs", "*"))):
        try:
            m = json.load(open(os.path.join(d, "meta.json"))); g = json.load(open(os.path.join(d, "grade.json")))
        except Exception:
            continue
        if m.get("rep", 1) < 1 or m.get("limit"): continue
        arm = m["arm"] if arm_map is None else arm_map.get(m["arm"])
        if arm: runs[(m["story"], m["agent"], arm)].append((m, g, d))
    return runs

runs = load(H)

def ok(rs): return [bool(g.get("PASS")) and m["exit_code"] == 0 for m, g, _ in rs]
def cell(rs):
    o = ok(rs); return f"{sum(o)}/{len(o)}" if o else "·"
def pool(R, agents, arm, stories=STORIES): return ok([r for s in stories for a in agents for r in R.get((s, a, arm), [])])
def rate(xs): return sum(xs) / len(xs) if xs else float("nan")
def boot(f, pools, n=4000, seed=11):
    rnd = random.Random(seed); vals = []
    for _ in range(n):
        vals.append(f(*[[rnd.choice(p) for _ in p] if p else [] for p in pools]))
    vals.sort(); return vals[int(0.025 * n)], vals[int(0.975 * n)]
def pp(x): return "·" if x != x else f"{x*100:+.0f} pp"

print("# Round 11 tables\n")
print("## Passes per agent and arm (five stories × five repetitions = 25 runs per cell when complete)\n")
print("| agent | none | story | ticket |\n|---|---|---|---|")
for a in AG:
    print(f"| {a} | " + " | ".join(cell([r for s in STORIES for r in runs.get((s, a, arm), [])]) for arm in ARMS) + " |")
print()
print("## The new stories only (n4, n6, n10: 15 runs per cell when complete), with the references\n")
print("| agent | none | story | ticket |\n|---|---|---|---|")
for a in AG + REF:
    print(f"| {a} | " + " | ".join(cell([r for s in MATTER for r in runs.get((s, a, arm), [])]) for arm in ARMS) + " |")
print()
print("## Works, but on the old package (n6 WORKS_ON_OLD_SDK, n10 WORKS_ON_PRISMA7), runs per arm\n")
print("| agent | story | none | story arm | ticket |\n|---|---|---|---|---|")
for a in AG + REF:
    for s, k in [("n6", "WORKS_ON_OLD_SDK"), ("n10", "WORKS_ON_PRISMA7")]:
        cs = [runs.get((s, a, arm), []) for arm in ARMS]
        if any(cs): print(f"| {a} | {s} | " + " | ".join(f"{sum(bool(g.get(k)) for _, g, _ in c)}/{len(c)}" if c else "·" for c in cs) + " |")
print()

print("## Passes per story and arm, all round 11 agents except kimi-k31\n")
print("| story | none | story | ticket |\n|---|---|---|---|")
for s in STORIES:
    print(f"| {s} {STORY[s]} | " + " | ".join(cell([r for a in AG[:4] for r in runs.get((s, a, arm), [])]) for arm in ARMS) + " |")
print()

print("## Per cell (the heatmap)\n")
for s in STORIES:
    print(f"### {s}: {STORY[s]}\n\n| agent | none | story | ticket |\n|---|---|---|---|")
    for a in AG + (REF if s in MATTER else []): print(f"| {a} | " + " | ".join(cell(runs.get((s, a, arm), [])) for arm in ARMS) + " |")
    print()

print("## The three questions (plan.md), with 95% bootstrap intervals\n")
print("| question | comparison | value | 95% CI |\n|---|---|---|---|")
opus_none = pool(runs, ["claude-opus"], "none", MATTER)
for a in OPEN:
    st = pool(runs, [a], "story", MATTER)
    if st and opus_none:
        f = lambda x, y: rate(x) - rate(y); lo, hi = boot(f, [st, opus_none])
        print(f"| A: open + story vs frontier alone | {a} story ({sum(st)}/{len(st)}) − Opus none, n4/n6/n10 ({sum(opus_none)}/{len(opus_none)}) | {pp(f(st, opus_none))} | {pp(lo)} to {pp(hi)} |")
for arm in ["none", "story"]:
    new, old = pool(runs, ["codex-oss"], arm, MATTER), pool(runs, ["agy-oss"], arm, MATTER)
    if new and old:
        f = lambda x, y: rate(x) - rate(y); lo, hi = boot(f, [new, old])
        print(f"| B: GPT-OSS harness | codex-oss {arm} ({sum(new)}/{len(new)}) − agy-oss {arm}, n4/n6/n10 ({sum(old)}/{len(old)}) | {pp(f(new, old))} | {pp(lo)} to {pp(hi)} |")
for label, ags in [(a, [a]) for a in AG] + [("all four round 11 agents", AG[:4])]:
    st, tk = pool(runs, ags, "story", MATTER), pool(runs, ags, "ticket", MATTER)
    if st and tk:
        f = lambda x, y: rate(x) - rate(y); lo, hi = boot(f, [st, tk])
        print(f"| C: story vs ticket, n4/n6/n10 | {label}: story {sum(st)}/{len(st)}, ticket {sum(tk)}/{len(tk)} | {pp(f(st, tk))} | {pp(lo)} to {pp(hi)} |")
print()

print("## Cost of the OpenRouter lanes\n")
print("Vibe: `cost_usd` from its export. Codex: token usage from `turn.completed` events × OpenRouter's price.\n")
print("| agent | arm | runs | tokens in (cached) / out | cost $ | $ per run |\n|---|---|---|---|---|---|")
for a in OPEN:
    for arm in ARMS:
        rs = [r for s in STORIES for r in runs.get((s, a, arm), [])]
        if not rs: continue
        tin = tca = tout = 0; cost = 0.0
        for m, g, d in rs:
            if a == "vibe-devstral":
                try:
                    e = json.load(open(os.path.join(d, "vibe", "export.json"))); u = e.get("usage") or {}
                    tin += u.get("input_tokens", 0); tca += u.get("cached_input_tokens", 0); tout += u.get("output_tokens", 0)
                    cost += e.get("cost_usd") or 0.0
                except Exception: pass
            else:
                for line in open(os.path.join(d, "agent.log"), errors="ignore"):
                    if '"turn.completed"' in line:
                        try: u = json.loads(line).get("usage", {})
                        except ValueError: continue
                        tin += u.get("input_tokens", 0); tca += u.get("cached_input_tokens", 0); tout += u.get("output_tokens", 0)
                pi, po = PRICE[a]; cost = tin / 1e6 * pi + tout / 1e6 * po
        print(f"| {a} | {arm} | {len(rs)} | {tin:,} ({tca:,}) / {tout:,} | {cost:.2f} | {cost/len(rs):.3f} |")
print()

WEB = {"claude": r'"name":"(?:WebSearch|WebFetch)"', "codex": r'(?m)^.*"item\.completed".*"type":"web_search".*$',
       "vibe": r'"(?:name|tool_name|tool)":\s*"(?:web_search|web_fetch)"', "kimi": r'"name":"(?:WebSearch|FetchURL)"',
       "agy": r'"tool_name":"(?:search_web|read_url_content)"'}
def web_calls(m, d):
    h = m["agent"].split("-")[0]; h = {"claude": "claude", "codex": "codex", "vibe": "vibe", "kimi": "kimi", "agy": "agy"}[h]
    try: txt = open(os.path.join(d, "agent.log"), errors="ignore").read()
    except OSError: return 0
    return len(re.findall(WEB[h], txt))
print("## Web use: runs with at least one web search or fetch (calls), per agent and arm\n")
print("| agent | " + " | ".join(ARMS) + " |\n|---|" + "---|" * len(ARMS))
for a in AG + REF:
    row = []
    for arm in ARMS:
        cs = [web_calls(m, d) for s in STORIES for m, _, d in runs.get((s, a, arm), [])]
        row.append(f"{sum(1 for c in cs if c)}/{len(cs)} ({sum(cs)})" if cs else "·")
    print(f"| {a} | " + " | ".join(row) + " |")
print()

print("## Wall time: mean seconds per run\n")
print("| agent | " + " | ".join(ARMS) + " |\n|---|" + "---|" * len(ARMS))
for a in AG + REF:
    row = []
    for arm in ARMS:
        ts = [m["wall_s"] for s in STORIES for m, _, _ in runs.get((s, a, arm), [])]
        row.append(str(round(sum(ts) / len(ts))) if ts else "·")
    print(f"| {a} | " + " | ".join(row) + " |")
print()

print("## Runs that are not results, and key scrubbing\n")
bad = [m for rs in runs.values() for m, g, _ in rs if m["exit_code"] != 0]
print("\n".join(f"- {m['id']}: exit {m['exit_code']} ({'timeout' if m['exit_code'] == 124 else 'error'}), {m['wall_s']} s" for m in bad) or "none")
hits = [m for rs in runs.values() for m, g, _ in rs if m.get("key_hits")]
print("\nRuns where the OpenRouter key was found and scrubbed: " + (", ".join(f"{m['id']} ({m['key_hits']})" for m in hits) or "none"))
