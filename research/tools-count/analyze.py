#!/usr/bin/env python3
"""Analyse results.csv -> tables.md + charts/*.png.  usage: .venv/bin/python analyze.py [phase]"""
import csv, json, math, os, sys, statistics as st
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PHASE = sys.argv[1] if len(sys.argv) > 1 else "full"
rows = [r for r in csv.DictReader(open(os.path.join(HERE, "results.csv"))) if r["phase"] == PHASE]
B = lambda x: x == "True"
F = lambda x: float(x) if x not in ("", None, "None") else None
MODELS = [m for m in ("claude", "codex", "gemini") if any(r["model"] == m for r in rows)]
VARS = sorted({r["variant"] for r in rows if r["variant"] != "GROUPED"}, key=int) + (["GROUPED"] if any(r["variant"] == "GROUPED" for r in rows) else [])
LABEL = {"claude": "Claude Opus 5.5 (Claude Code)", "codex": "GPT-6.1-sol (Codex CLI default)", "gemini": "Gemini 3.1 Pro (Antigravity)"}

def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 2
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)

def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None

cell = defaultdict(list)
for r in rows:
    cell[(r["model"], r["variant"])].append(r)

out = []
def P(s=""): out.append(s)

P(f"# Tables ({PHASE})\n")
P("Status counts per model (ok = scored; error/timeout = counted as failures in accuracy; ratelimited = missing, excluded):\n")
P("| model | ok | error | timeout | ratelimited (missing) |"); P("|---|---|---|---|---|")
for m in MODELS:
    c = defaultdict(int)
    for r in rows:
        if r["model"] == m: c[r["status"]] += 1
    P(f"| {m} | {c['ok']} | {c['error']} | {c['timeout']} | {c['ratelimited']} |")
P()

summary = {}
for m in MODELS:
    P(f"## {LABEL[m]}\n")
    P("| tools | runs | success | 95% CI | right tools | right args | runs with a wrong tool | wrong (ambiguous tasks) | calls/run | failed calls/run | first-call input tok | input tok/run | output tok/run | wall s | cost $/run |")
    P("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for v in VARS:
        rs = [r for r in cell[(m, v)] if r["status"] != "ratelimited"]
        if not rs: continue
        n = len(rs); k = sum(B(r["success"]) for r in rs)
        lo, hi = wilson(k, n)
        amb = [r for r in rs if r["kind"] == "ambiguous"]
        okr = [r for r in rs if r["status"] == "ok"]
        s = {"n": n, "success": k / n, "ci": (lo, hi), "tools_ok": sum(B(r["tools_ok"]) for r in rs) / n,
             "args_ok": sum(B(r["args_ok"]) for r in rs) / n, "wrong_rate": sum(int(r["wrong_calls"] or 0) > 0 for r in rs) / n,
             "wrong_amb": (sum(int(r["wrong_calls"] or 0) > 0 for r in amb) / len(amb)) if amb else None,
             "calls": mean([F(r["n_calls"]) for r in okr]), "errc": mean([F(r["error_calls"]) for r in okr]), "first": mean([F(r["first_call_input"]) for r in okr]),
             "input": mean([F(r["input_tokens_total"]) for r in okr]), "output": mean([F(r["output_tokens"]) for r in okr]),
             "wall": mean([F(r["wall_s"]) for r in okr]), "cost": mean([F(r["cost_usd"]) for r in okr])}
        summary[(m, v)] = s
        fmt = lambda x, f="{:.0f}": "" if x is None else f.format(x)
        P(f"| {v} | {n} | {s['success']:.0%} | {lo:.0%}–{hi:.0%} | {s['tools_ok']:.0%} | {s['args_ok']:.0%} | {s['wrong_rate']:.0%} | "
          f"{fmt(s['wrong_amb'], '{:.0%}')} | {fmt(s['calls'], '{:.2f}')} | {fmt(s['errc'], '{:.2f}')} | {fmt(s['first'])} | {fmt(s['input'])} | {fmt(s['output'])} | "
          f"{fmt(s['wall'], '{:.1f}')} | {fmt(s['cost'], '{:.4f}')} |")
    P()
    # linear fit of tokens vs N (separate tools only)
    for key, lab in (("first", "first-call input tokens"), ("input", "input tokens per run")):
        pts = [(int(v), summary[(m, v)][key]) for v in VARS if v != "GROUPED" and int(v) <= 50 and (m, v) in summary and summary[(m, v)][key] is not None]
        if len(pts) >= 3:
            xs, ys = zip(*pts); mx, my = st.mean(xs), st.mean(ys)
            b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x in xs); a = my - b * mx
            ss_res = sum((y - (a + b * x)) ** 2 for x, y in pts); ss_tot = sum((y - my) ** 2 for y in ys)
            r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
            extra = ""
            for v in ("75", "100"):
                if (m, v) in summary and summary[(m, v)][key] is not None:
                    pred = a + b * int(v); act = summary[(m, v)][key]
                    extra += f"; at N={v}: predicted {pred:.0f}, measured {act:.0f} ({(act - pred) / pred:+.1%})"
            P(f"- Linear fit on N = 5–50, {lab} = {a:.0f} + {b:.1f} × N  (R² = {r2:.3f}){extra}")
            summary[(m, "fit_" + key)] = {"a": a, "b": b, "r2": r2}
    P()

# failures listing
P("## Every failed run\n")
P("| model | tools | task | kind | rep | status | called (canonical ops) | why |"); P("|---|---|---|---|---|---|---|---|")
for r in sorted(rows, key=lambda r: (r["model"], r["task"], VARS.index(r["variant"]) if r["variant"] in VARS else 99, r["rep"])):
    if r["status"] == "ratelimited" or B(r["success"]): continue
    why = []
    if r["status"] != "ok": why.append(r["status"] + ": " + (r["harness_error"] or "")[:80])
    if not B(r["tools_ok"]): why.append("expected tool(s) missing/out of order")
    elif not B(r["args_ok"]): why.append("key args wrong")
    if int(r["wrong_calls"] or 0): why.append("wrong tool: " + r["wrong_ops"])
    P(f"| {r['model']} | {r['variant']} | {r['task']} | {r['kind']} | {r['rep']} | {r['status']} | {r['called_ops'] or '(none)'} | {'; '.join(why)} |")
P()

# per task success matrix
P("## Success by task (share of runs, all variants pooled)\n")
tasks = sorted({r["task"] for r in rows})
P("| task | kind | " + " | ".join(MODELS) + " |"); P("|---|---|" + "---|" * len(MODELS))
for t in tasks:
    kind = next(r["kind"] for r in rows if r["task"] == t)
    cells = []
    for m in MODELS:
        rs = [r for r in rows if r["task"] == t and r["model"] == m and r["status"] != "ratelimited"]
        cells.append(f"{sum(B(r['success']) for r in rs)}/{len(rs)}" if rs else "")
    P(f"| {t} | {kind} | " + " | ".join(cells) + " |")
P()
open(os.path.join(HERE, f"tables-{PHASE}.md"), "w").write("\n".join(out) + "\n")
json.dump({f"{k[0]}|{k[1]}": v for k, v in summary.items()}, open(os.path.join(HERE, f"summary-{PHASE}.json"), "w"), indent=1, default=str)

# ---------------- charts ----------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib missing; tables only"); sys.exit(0)
os.makedirs(os.path.join(HERE, "charts"), exist_ok=True)
COL = {"claude": "#2a78d6", "codex": "#eb6834", "gemini": "#1baf7a"}
MK = {"claude": "o", "codex": "s", "gemini": "^"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb"})
NS = [int(v) for v in VARS if v != "GROUPED"]
GX = (max(NS) + 10) if NS else 0

def chart(fname, key, ylabel, title, pct=False, ylim=None, ci=False):
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    gap = any(n > 50 for n in NS) and not any(50 < n < 75 for n in NS)
    if gap:  # sizes 55-70 were not run: shade them and draw the 50 -> 75 link dashed
        ax.axvspan(52.5, 72.5, color=GRID, alpha=0.45, lw=0)
        ax.text(62.5, 0.02, "55–70\nnot run", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8, color=MUTED)
    for m in MODELS:
        xs = [n for n in NS if (m, str(n)) in summary and summary[(m, str(n))][key] is not None]
        ys = [summary[(m, str(n))][key] for n in xs]
        if not xs: continue
        lo_x = [x for x in xs if x <= 50]; hi_x = [x for x in xs if x >= 75]
        y = dict(zip(xs, ys))
        ax.plot(lo_x, [y[x] for x in lo_x], color=COL[m], lw=2, marker=MK[m], ms=6, label=LABEL[m])
        if hi_x:
            ax.plot(hi_x, [y[x] for x in hi_x], color=COL[m], lw=2, marker=MK[m], ms=6)
            if lo_x: ax.plot([lo_x[-1], hi_x[0]], [y[lo_x[-1]], y[hi_x[0]]], color=COL[m], lw=1.5, ls=(0, (3, 3)))
        if ci:
            lo = [summary[(m, str(n))]["ci"][0] for n in xs]; hi = [summary[(m, str(n))]["ci"][1] for n in xs]
            ax.fill_between(xs, lo, hi, color=COL[m], alpha=0.10, lw=0)
        g = summary.get((m, "GROUPED"))
        if g and g[key] is not None:
            ax.plot([GX], [g[key]], color=COL[m], marker=MK[m], ms=8, mfc="white", mew=2, ls="none")
    if NS:
        ax.axvline(max(NS) + 5, color=GRID, lw=1)
        ax.set_xticks(NS + [GX]); ax.set_xticklabels([str(n) for n in NS] + ["7\ngrouped"], fontsize=8.5)
    ax.set_xlabel("tools exposed by the MCP server"); ax.set_ylabel(ylabel); ax.set_title(title, loc="left", color=INK, fontsize=11)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    if pct:
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    if ylim: ax.set_ylim(*ylim)
    else: ax.set_ylim(bottom=0)
    ax.legend(frameon=False, fontsize=9, loc="best")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "charts", fname), dpi=150); plt.close(fig)

sfx = "" if PHASE == "full" else f"-{PHASE}"
chart(f"accuracy-vs-n{sfx}.png", "success", "runs fully correct", "Accuracy vs number of tools (all three lines overlap at 100%; shaded: 95% CI)", pct=True, ylim=(0, 1.05), ci=True)
chart(f"first-call-tokens-vs-n{sfx}.png", "first", "input tokens, first model call", "Context cost of the tool list (first call)")
chart(f"input-tokens-vs-n{sfx}.png", "input", "input tokens per run (all calls)", "Input tokens per run")
chart(f"wrong-ambiguous-vs-n{sfx}.png", "wrong_amb", "ambiguous-task runs with a wrong tool", "Wrong-tool rate on ambiguous tasks", pct=True, ylim=(0, 1.05))
chart(f"wall-vs-n{sfx}.png", "wall", "seconds per run", "Wall time per run")
print("ok", PHASE, len(rows), "rows")
