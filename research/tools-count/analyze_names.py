#!/usr/bin/env python3
"""Vague names vs honest names (same tools, descriptions, schemas, tasks).
Honest = phase "full", vague = phase "vague" (TC_NAMES=vague), N = 50 and 100.
-> tables-vague.md, summary-vague.json, charts/names-*.png.   usage: .venv/bin/python analyze_names.py"""
import csv, json, math, os, statistics as st
from collections import Counter, defaultdict

H = os.path.dirname(os.path.abspath(__file__))
ALL = list(csv.DictReader(open(os.path.join(H, "results.csv"))))
VN = json.load(open(os.path.join(H, "vague-names.json")))["names"]
LANES = [m for m in ("claude-search", "claude", "gemini", "codex") if any(r["phase"] == "vague" and r["model"] == m for r in ALL)]
NS = ["50", "100"]
LAB = {"claude-search": "Claude Code, tool search on (default)", "claude": "Claude Code, tool search off (all schemas upfront)",
       "gemini": "Antigravity (Gemini 3.1 Pro)", "codex": "Codex CLI (gpt-6.1-sol)"}
B = lambda x: x == "True"
F = lambda x: float(x) if x not in ("", None, "None") else None
I = lambda x: int(float(x)) if x not in ("", None, "None") else 0

def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None

def wilson(k, n, z=1.96):
    if not n: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

def rows(m, names, v):
    ph = "vague" if names == "vague" else "full"
    return [r for r in ALL if r["phase"] == ph and r["model"] == m and r["variant"] == v and r["status"] != "ratelimited"]

S = {}
for m in LANES:
    for names in ("honest", "vague"):
        for v in NS:
            rs = rows(m, names, v)
            if not rs: continue
            ok = [r for r in rs if r["status"] == "ok"]; n = len(rs); k = sum(B(r["success"]) for r in rs)
            s = dict(n=n, k=k, success=k / n, ci=wilson(k, n), status=dict(Counter(r["status"] for r in rs)),
                     wrong_exec_runs=sum(I(r["wrong_calls"]) > 0 for r in rs), wrong_pick_runs=sum(I(r["wrong_tool_picks"]) > 0 for r in rs),
                     wrong_picks=sum(I(r["wrong_tool_picks"]) for r in rs), first_pick_wrong=sum(B(r["first_pick_wrong"]) for r in rs),
                     failed_calls=mean([F(r["error_calls"]) for r in ok]), calls=mean([F(r["n_calls"]) for r in ok]),
                     first=mean([F(r["first_call_input"]) for r in ok]), input=mean([F(r["input_tokens_total"]) for r in ok]),
                     output=mean([F(r["output_tokens"]) for r in ok]), model_calls=mean([F(r["model_calls"]) for r in ok]),
                     wall=mean([F(r["wall_s"]) for r in ok]), cost=mean([F(r["cost_usd"]) for r in ok]),
                     builtin=sum(I(r["builtin_calls"]) for r in rs), n_ok=len(ok))
            if m == "claude-search":
                s.update(ts=mean([F(r["toolsearch_calls"]) for r in ok]), ts_kw=mean([F(r["toolsearch_keyword"]) for r in ok]),
                         kw_runs=sum(I(r["toolsearch_keyword"]) > 0 for r in ok), loaded=mean([F(r["toolsearch_loaded"]) for r in ok]),
                         extra=mean([F(r["loaded_extra"]) for r in ok]), first_load_wrong=sum(B(r["first_load_wrong"]) for r in ok),
                         notfound=sum(bool(r["needed_not_found"]) for r in ok), hid=sum(B(r["search_hid_tool"]) for r in ok))
            if m == "gemini":
                s.update(reads=mean([F(r["schema_reads"]) or 0 for r in ok]), loaded=mean([len([x for x in r["loaded_tools"].split("|") if x]) for r in ok]),
                         extra=mean([F(r["loaded_extra"]) or 0 for r in ok]), first_load_wrong=sum(B(r["first_load_wrong"]) for r in ok),
                         skipped=sum(I(r["schema_reads"]) == 0 for r in ok))
            S[(m, names, v)] = s

out = []
P = out.append
pc = lambda x: "n/a" if x is None else f"{x:.0%}"
k0 = lambda x: "n/a" if x is None else f"{x/1000:.1f}k"
f2 = lambda x: "n/a" if x is None else f"{x:.2f}"
P("# Tables: vague names vs honest names (N = 50, 100)\n")
P("Honest = the original runs (phase `full`); vague = the same tools, descriptions, schemas and tasks under the names in "
  "`vague-names.json` (phase `vague`, `TC_NAMES=vague`). 18 tasks × 2 reps per cell. Scored by canonical operation.\n")
P("## Accuracy and wrong picks\n")
P("| lane | tools | names | runs | fully correct | 95% CI | runs with a wrong tool executed | runs with any wrong pick (executed or failed) | wrong picks | first mutating pick wrong | failed calls/run | calls/run | status |")
P("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for m in LANES:
    for v in NS:
        for names in ("honest", "vague"):
            s = S.get((m, names, v))
            if not s: continue
            P(f"| {m} | {v} | {names} | {s['n']} | {s['k']}/{s['n']} ({s['success']:.0%}) | {s['ci'][0]:.0%}–{s['ci'][1]:.0%} | {s['wrong_exec_runs']} | {s['wrong_pick_runs']} | {s['wrong_picks']} | "
              f"{s['first_pick_wrong']} | {f2(s['failed_calls'])} | {f2(s['calls'])} | {', '.join(f'{a} {b}' for a, b in s['status'].items())} |")
P("")
P("## Schema loading\n")
P("claude-search: `ToolSearch` calls; keyword = free-text search (not `select:` by exact name); loaded = distinct tools returned by the searches; "
  "extra = loaded tools that are neither needed nor read-only; first load wrong = the first search returned no needed tool. "
  "gemini: reads of the lazy schema files; skipped = runs that read no schema at all.\n")
P("| lane | tools | names | ToolSearch calls/run | keyword searches/run | runs with a keyword search | schema reads/run | distinct schemas loaded/run | extra (not needed) loaded/run | runs whose first load was wrong | runs that never loaded a needed tool | runs with no schema read |")
P("|---|---|---|---|---|---|---|---|---|---|---|---|")
for m in ("claude-search", "gemini"):
    if m not in LANES: continue
    for v in NS:
        for names in ("honest", "vague"):
            s = S.get((m, names, v))
            if not s: continue
            if m == "claude-search":
                P(f"| {m} | {v} | {names} | {f2(s['ts'])} | {f2(s['ts_kw'])} | {s['kw_runs']}/{s['n_ok']} | – | {f2(s['loaded'])} | {f2(s['extra'])} | {s['first_load_wrong']} | {s['notfound']} | – |")
            else:
                P(f"| {m} | {v} | {names} | – | – | – | {f2(s['reads'])} | {f2(s['loaded'])} | {f2(s['extra'])} | {s['first_load_wrong']} | – | {s['skipped']}/{s['n_ok']} |")
P("")
P("## Tokens, calls, time\n")
P("| lane | tools | names | first-call input | input/run | output/run | model calls/run | wall s | $/run (list) |")
P("|---|---|---|---|---|---|---|---|---|")
for m in LANES:
    for v in NS:
        for names in ("honest", "vague"):
            s = S.get((m, names, v))
            if not s: continue
            P(f"| {m} | {v} | {names} | {k0(s['first'])} | {k0(s['input'])} | {s['output']:.0f} | {f2(s['model_calls'])} | {s['wall']:.1f} | {'' if s['cost'] is None else format(s['cost'], '.3f')} |")
P("")

# confusions: which vague name was picked for which task
conf = Counter(); conf_tasks = defaultdict(Counter)
for r in ALL:
    if r["phase"] != "vague" or r["status"] == "ratelimited": continue
    for op in [x for x in r["wrong_ops"].split("|") if x]:
        conf[(r["task"], op, "executed")] += 1; conf_tasks[r["model"]][(r["task"], op)] += 1
    for op in [x for x in r["wrong_attempt_ops"].split("|") if x]:
        conf[(r["task"], op, "failed")] += 1; conf_tasks[r["model"]][(r["task"], op)] += 1
TASKS = {t["id"]: t for t in json.load(open(os.path.join(H, "tasks.json")))["tasks"]}
P("## Confusions with vague names (wrong tool picked, all lanes)\n")
P("| task | needed (vague name ← honest) | picked instead (vague name ← honest op) | executed | failed attempt | lanes |")
P("|---|---|---|---|---|---|")
for (t, op) in sorted({(a, b) for a, b, _ in conf}, key=lambda x: -(conf[(x[0], x[1], "executed")] + conf[(x[0], x[1], "failed")])):
    need = ", ".join(f"`{VN[s['tool']]}` ← {s['tool']}" for s in TASKS[t]["expected"])
    lanes = ", ".join(f"{m} {c[(t, op)]}" for m, c in conf_tasks.items() if c[(t, op)])
    P(f"| {t} | {need} | `{VN.get(op, op)}` ← {op} | {conf[(t, op, 'executed')]} | {conf[(t, op, 'failed')]} | {lanes} |")
if not conf: P("| – | – | none | 0 | 0 | – |")
P("")
# first schema loaded wrong: which one
fl = Counter()
for r in ALL:
    if r["phase"] == "vague" and B(r["first_load_wrong"]):
        first = (r["loaded_tools"].split("|") or [""])[0]
        fl[(r["model"], r["task"], first)] += 1
P("## First schema loaded was not a needed tool (vague runs)\n")
P("| lane | task | first loaded (vague ← honest) | runs |"); P("|---|---|---|---|")
for (m, t, x), c in sorted(fl.items(), key=lambda kv: (-kv[1], kv[0])):
    P(f"| {m} | {t} | `{VN.get(x, x)}` ← {x} | {c} |")
if not fl: P("| – | – | none | 0 |")
P("")
# keyword queries
P("## Keyword ToolSearch queries with vague names (claude-search)\n")
P("| tools | task | rep | queries | loaded (honest) | success |"); P("|---|---|---|---|---|---|")
for r in sorted([r for r in ALL if r["phase"] == "vague" and r["model"] == "claude-search" and I(r["toolsearch_keyword"]) > 0],
                key=lambda r: (int(r["variant"]), r["task"], r["rep"])):
    P(f"| {r['variant']} | {r['task']} | {r['rep']} | `{r['toolsearch_queries']}` | {r['loaded_tools'].replace('|', ', ')} | {r['success']} |")
P("")
# every failed vague run
P("## Every failed vague run\n")
P("| lane | tools | task | rep | status | called (vague names) | canonical ops | why |"); P("|---|---|---|---|---|---|---|---|")
for r in sorted([r for r in ALL if r["phase"] == "vague" and r["status"] != "ratelimited" and not B(r["success"])], key=lambda r: (r["model"], r["task"], int(r["variant"]), r["rep"])):
    why = []
    if r["status"] != "ok": why.append(r["status"] + ": " + (r["harness_error"] or "")[:80])
    if not B(r["tools_ok"]): why.append("expected tool(s) missing/out of order")
    elif not B(r["args_ok"]): why.append("key args wrong")
    if I(r["wrong_calls"]): why.append("wrong tool executed: " + r["wrong_ops"])
    called = [VN.get(x, x) for x in r["called_ops"].split("|") if x]
    P(f"| {r['model']} | {r['variant']} | {r['task']} | {r['rep']} | {r['status']} | {', '.join(called) or '(none)'} | {r['called_ops'].replace('|', ', ') or '(none)'} | {'; '.join(why)} |")
P("")
P("## Success by task, vague names (N = 50 and 100 pooled)\n")
P("| task | kind | needed (vague) | " + " | ".join(LANES) + " |"); P("|---|---|---|" + "---|" * len(LANES))
for t in sorted(TASKS):
    cells = []
    for m in LANES:
        rs = [r for r in ALL if r["phase"] == "vague" and r["model"] == m and r["task"] == t and r["status"] != "ratelimited"]
        cells.append(f"{sum(B(r['success']) for r in rs)}/{len(rs)}" if rs else "")
    P(f"| {t} | {TASKS[t]['kind']} | {', '.join(VN[s['tool']] for s in TASKS[t]['expected'])} | " + " | ".join(cells) + " |")
open(os.path.join(H, "tables-vague.md"), "w").write("\n".join(out) + "\n")
json.dump({"|".join(k): v for k, v in S.items()} | {"_confusions": {f"{a}|{b}|{c}": n for (a, b, c), n in conf.items()}},
          open(os.path.join(H, "summary-vague.json"), "w"), indent=1, default=str)

# ---------------- charts: honest vs vague, paired bars per lane x N ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK, MUTED, GRID, BG = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
HON, VAG = "#9fb8d9", "#c2410c"   # honest = quiet blue-gray, vague = orange
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": BG, "axes.facecolor": BG})
SHORT = {"claude-search": "Claude Code\nsearch on", "claude": "Claude Code\nsearch off", "gemini": "Antigravity\n(Gemini)", "codex": "Codex"}

def paired(fname, key, ylabel, title, lanes=LANES, pct=False, ylim=None, fmt="{:.0f}"):
    groups = [(m, v) for m in lanes for v in NS if (m, "vague", v) in S]
    fig, ax = plt.subplots(figsize=(max(6.4, 1.25 * len(groups) + 1.5), 4.2))
    w = 0.38
    for i, (m, v) in enumerate(groups):
        for j, (names, col) in enumerate((("honest", HON), ("vague", VAG))):
            s = S.get((m, names, v)); y = None if not s else s[key]
            if y is None: continue
            x = i + (j - 0.5) * (w + 0.02)
            ax.bar(x, y, w, color=col, edgecolor=BG, linewidth=1, label=names + " names" if i == 0 else None)
            ax.text(x, y, (f"{y:.0%}" if pct else fmt.format(y)), ha="center", va="bottom", fontsize=7.5, color=MUTED)
    ax.set_xticks(range(len(groups))); ax.set_xticklabels([f"{SHORT[m]}\nN = {v}" for m, v in groups], fontsize=8)
    ax.set_ylabel(ylabel); ax.set_title(title, loc="left", color=INK, fontsize=11)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    if pct: ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    if ylim: ax.set_ylim(*ylim)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, -0.22), ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(H, "charts", fname), dpi=150); plt.close(fig)

paired("names-accuracy.png", "success", "runs fully correct", "Accuracy: honest vs vague tool names", pct=True, ylim=(0, 1.12))
paired("names-input-tokens.png", "input", "input tokens per run", "Input tokens per run: honest vs vague names", fmt="{:,.0f}")
paired("names-schema-loads.png", "loaded", "distinct schemas loaded per run", "Schemas the agent loaded before acting",
       lanes=[m for m in ("claude-search", "gemini") if m in LANES], fmt="{:.1f}")
paired("names-wall.png", "wall", "seconds per run", "Wall time per run: honest vs vague names", fmt="{:.1f}")
print("ok", {"|".join(k): (v["k"], v["n"]) for k, v in S.items()})
