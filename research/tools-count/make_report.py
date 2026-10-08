#!/usr/bin/env python3
"""Fill report.template.md with numbers from results.csv / summary-full.json -> report.md"""
import csv, json, os, re, math, statistics as st, sys
from collections import defaultdict
H = os.path.dirname(os.path.abspath(__file__))
rows = [r for r in csv.DictReader(open(os.path.join(H, "results.csv"))) if r["phase"] == "full"]
S = {tuple(k.split("|")): v for k, v in json.load(open(os.path.join(H, "summary-full.json"))).items()}
counted = [r for r in rows if r["status"] != "ratelimited"]
NS = [str(n) for n in range(5, 55, 5)]
NX = NS + ["75", "100"]  # 55-70 were not run
def s(m, v, k): return S.get((m, v), {}).get(k)
def k0(x): return f"{x/1000:.1f}k" if x is not None else "n/a"
def pct(x): return f"{x:.0%}" if x is not None else "n/a"
def cell(m, v):
    x = S.get((m, v)); return f"{x['success']:.0%} ({x['n']})" if x else "n/a"
F = {}
F["TOTAL_RUNS"] = f"{len(counted):,}"
search_rows = [r for r in counted if r["model"] == "claude-search"]
counted = [r for r in counted if r["model"] != "claude-search"]   # the original three lanes; claude-search is reported on its own
F["ORIG_RUNS"] = f"{len(counted):,}"; F["CS_RUNS"] = str(len(search_rows))
sep = [r for r in counted if r["variant"] != "GROUPED" and int(r["variant"]) <= 50]
sep100 = [r for r in counted if r["variant"] in ("75", "100")]
sep_fail = [r for r in sep if r["success"] != "True"]
by_m = {m: len([r for r in sep if r["model"] == m]) for m in ("claude", "codex", "gemini")}
F["SEP_RUNS"] = str(len(sep))
F["SEP_FAIL_SENTENCE"] = (f"All {len(sep):,} runs with separate tools were fully correct (Claude {by_m['claude']}, Codex {by_m['codex']}, Gemini {by_m['gemini']})." if not sep_fail
                          else f"{len(sep)-len(sep_fail):,} of {len(sep):,} separate-tool runs were fully correct.")
s100f = [r for r in sep100 if r["success"] != "True"]
F["SEP100_SENTENCE"] = (f"The same held at 75 and 100 tools: {len(sep100) - len(s100f)} of {len(sep100)} runs were fully correct." if sep100 else "")
F["SEP_FAIL_SHORT"] = f"There were {len(sep_fail) + len(s100f)} failures in {len(sep) + len(sep100):,} separate-tool runs."
fc, fi = S[("claude", "fit_first")], S[("claude", "fit_input")]
F.update(C_FIRST_A=f"{fc['a']:,.0f}", C_FIRST_B=f"{fc['b']:.0f}", C_FIRST_R2=f"{fc['r2']:.3f}", C_IN_A=f"{fi['a']:,.0f}", C_IN_B=f"{fi['b']:.0f}", C_IN_R2=f"{fi['r2']:.3f}",
         C_FIRST_5=k0(s("claude", "5", "first")), C_FIRST_50=k0(s("claude", "50", "first")), C_IN_5=k0(s("claude", "5", "input")), C_IN_50=k0(s("claude", "50", "input")),
         C_IN_25=k0(s("claude", "25", "input")), C_RATIO=f"{s('claude','50','input')/s('claude','5','input'):.1f}", C_FIRST_G=k0(s("claude", "GROUPED", "first")),
         C_EQUIV=f"{(s('claude','GROUPED','first')-fc['a'])/fc['b']:.0f}", C_IN_G=k0(s("claude", "GROUPED", "input")), C_ACC_G=pct(s("claude", "GROUPED", "success")),
         C_CALLS_G=f"{s('claude','GROUPED','calls'):.2f}", C_CALLS_50=f"{s('claude','50','calls'):.2f}", C_10=f"{fc['b']*10/1000:.1f}k")
F.update(C_FIRST_100=k0(s("claude", "100", "first")), C_IN_100=k0(s("claude", "100", "input")), C_RATIO100=f"{s('claude','100','input')/s('claude','5','input'):.1f}",
         X_IN_100=k0(s("codex", "100", "input")), G_IN_100=k0(s("gemini", "100", "input")))
xi = S[("codex", "fit_input")]
F.update(X_FIRST=f"{st.mean(s('codex', v, 'first') for v in NS if s('codex', v, 'first')):,.0f}", X_IN_B=f"{xi['b']:.0f}", X_IN_R2=f"{xi['r2']:.2f}",
         X_IN_5=k0(s("codex", "5", "input")), X_IN_50=k0(s("codex", "50", "input")), X_IN_25=k0(s("codex", "25", "input")), X_IN_G=k0(s("codex", "GROUPED", "input")),
         X_ACC_G=pct(s("codex", "GROUPED", "success")))
gf = S[("gemini", "fit_first")]
F.update(G_FIRST_B=f"{gf['b']:.0f}", G_FIRST_5=k0(s("gemini", "5", "first")), G_FIRST_50=k0(s("gemini", "50", "first")), G_IN_5=k0(s("gemini", "5", "input")),
         G_IN_45=k0(s("gemini", "45", "input")), G_IN_50=k0(s("gemini", "50", "input")), G_ACC_G=f"{s('gemini','GROUPED','success'):.0%} ({round(s('gemini','GROUPED','success')*s('gemini','GROUPED','n'))}/{s('gemini','GROUPED','n')})",
         G_IN_G=k0(s("gemini", "GROUPED", "input")), G_CALLS_G=f"{s('gemini','GROUPED','calls'):.1f}", G_ERRC_G=f"{s('gemini','GROUPED','errc'):.1f}",
         G_WALL_G=f"{s('gemini','GROUPED','wall'):.0f}", G_WRONG_AMB_G=pct(s("gemini", "GROUPED", "wrong_amb")), G_ERRC_50=f"{s('gemini','50','errc'):.1f}")
g50 = [r for r in rows if r["model"] == "gemini" and r["variant"] == "50"]
F["G_SKIP_50"] = str(sum(1 for r in g50 if int(r["schema_reads"] or 0) == 0))
cr = [r for r in counted if r["model"] == "claude" and r["cost_usd"]]
F["C_RUNS"] = str(len(cr)); F["C_COST_TOTAL"] = f"{sum(float(r['cost_usd']) for r in cr):.2f}"
costs = [s("claude", v, "cost") for v in NS + ["GROUPED"] if s("claude", v, "cost")]
F["C_COST_MIN"], F["C_COST_MAX"] = f"{min(costs):.3f}", f"{max(costs):.3f}"
def lab(v): return "GROUPED (7)" if v == "GROUPED" else v
GAPROW = lambda k: "| 55–70 | " + " | ".join(["not run"] * k) + " |"
def rows_with_gap(fn, k):
    out = []
    for v in NX + ["GROUPED"]:
        if v == "75": out.append(GAPROW(k))
        out.append(fn(v))
    return "\n".join(out)
F["ACC_TABLE"] = rows_with_gap(lambda v: f"| {lab(v)} | {cell('claude', v)} | {cell('claude-search', v) if S.get(('claude-search', v)) else 'not run'} | {cell('codex', v)} | {cell('gemini', v)} |", 4)
F["TOK_TABLE"] = rows_with_gap(lambda v: f"| {lab(v)} | " + " | ".join(f"{k0(s(m, v, 'first'))} | {k0(s(m, v, 'input'))}" if S.get((m, v)) else "not run | not run" for m in ("claude", "claude-search", "codex", "gemini")) + " |", 8)
ver = defaultdict(list)
for r in counted:
    if r["status"] == "ok": ver[(r["model"], r["variant"])].append(int(r["extra_readonly"] or 0) > 0)
for r in search_rows:
    if r["status"] == "ok": ver[(r["model"], r["variant"])].append(int(r["extra_readonly"] or 0) > 0)
MLAB = {"claude": "claude (search off)", "claude-search": "claude (search on)", "codex": "codex", "gemini": "gemini"}
M4 = ("claude", "claude-search", "codex", "gemini")
F["VERIFY_TABLE"] = "\n".join(f"| {MLAB[m]} | " + " | ".join(pct(sum(ver[(m, v)]) / len(ver[(m, v)])) if ver[(m, v)] else "n/a" for v in ("5", "10", "20", "30", "40", "50", "75", "100", "GROUPED")) + " |" for m in M4)
F["WALL_TABLE"] = "\n".join(f"| {MLAB[m]} | " + " | ".join(f"{s(m, v, 'wall'):.1f} s" if s(m, v, "wall") else "n/a" for v in ("5", "25", "50", "75", "100", "GROUPED")) + " |" for m in M4)
gt = ["| model | variant | fully correct | first-call input | input per run | calls/run | failed calls/run | wall s |", "|---|---|---|---|---|---|---|---|"]
for m in M4:
    for v in ("25", "50", "GROUPED"):
        x = S.get((m, v))
        if x: gt.append(f"| {MLAB[m]} | {v if v!='GROUPED' else 'GROUPED (7)'} | {x['success']:.0%} | {k0(x['first'])} | {k0(x['input'])} | {x['calls']:.2f} | {x['errc']:.2f} | {x['wall']:.1f} |")
F["GROUP_TABLE"] = "\n".join(gt)
miss = [r for r in rows if r["model"] == "codex" and r["status"] == "ratelimited"]
xn = len([r for r in counted if r["model"] == "codex"])
note_file = os.path.join(H, "codex-quota-note.txt")
F["CODEX_QUOTA_NOTE"] = open(note_file).read().strip() if os.path.exists(note_file) else ""
F["CODEX_QUOTA_NOTE"] += f" Final count: {xn} of 396 Codex runs scored; {396 - xn} missing."
# ---------- Claude Code with tool search on (default) vs off ----------
CSV = ["5", "10", "25", "50", "75", "100", "GROUPED"]
def x(m, v, k):
    return S.get((m, v), {}).get(k)
cs_ok = [r for r in search_rows if r["status"] == "ok"]
cs_succ = sum(r["success"] == "True" for r in search_rows)
F.update(CS_SUCC=f"{cs_succ} of {len(search_rows)}", CS_FAILS=str(len(search_rows) - cs_succ),
         CS_TS=f"{st.mean(int(r['toolsearch_calls'] or 0) for r in cs_ok):.2f}",
         CS_KW_RUNS=str(sum(int(r["toolsearch_keyword"] or 0) > 0 for r in cs_ok)),
         CS_OFF_RUNS=str(sum(int(r["toolsearch_offtarget"] or 0) > 0 for r in cs_ok)),
         CS_NF_RUNS=str(sum(bool(r["needed_not_found"]) for r in cs_ok)),
         CS_HID_RUNS=str(sum(r["search_hid_tool"] == "True" for r in cs_ok)),
         CS_BUILTIN=str(sum(int(r["builtin_calls"] or 0) for r in search_rows)),
         CS_TS_MIN=f"{min(x('claude-search', v, 'ts_calls') for v in CSV if x('claude-search', v, 'ts_calls') is not None):.2f}",
         CS_TS_MAX=f"{max(x('claude-search', v, 'ts_calls') for v in CSV if x('claude-search', v, 'ts_calls') is not None):.2f}")
for v in CSV:
    tag = "G" if v == "GROUPED" else v
    F[f"CS_FIRST_{tag}"] = k0(x("claude-search", v, "first")); F[f"CS_IN_{tag}"] = k0(x("claude-search", v, "input"))
    F[f"CS_MC_{tag}"] = f"{x('claude-search', v, 'model_calls'):.2f}" if x("claude-search", v, "model_calls") else "n/a"
    F[f"C_MC_{tag}"] = f"{x('claude', v, 'model_calls'):.2f}" if x("claude", v, "model_calls") else "n/a"
csf, csi = S.get(("claude-search", "fit_first")), S.get(("claude-search", "fit_input"))
F.update(CS_FIRST_B=f"{csf['b']:.0f}", CS_FIRST_A=f"{csf['a']:,.0f}", CS_FIRST_R2=f"{csf['r2']:.2f}", CS_IN_B=f"{csi['b']:.0f}", CS_IN_A=f"{csi['a']:,.0f}", CS_IN_R2=f"{csi['r2']:.2f}",
         CS_RATIO100=f"{x('claude-search','100','input')/x('claude-search','5','input'):.2f}",
         C_SAVE_FIRST_100=f"{1 - x('claude-search','100','first')/x('claude','100','first'):.0%}",
         C_SAVE_IN_100=f"{1 - x('claude-search','100','input')/x('claude','100','input'):.0%}",
         C_SAVE_IN_50=f"{1 - x('claude-search','50','input')/x('claude','50','input'):.0%}",
         C_EXTRA_IN_5=f"{x('claude-search','5','input')/x('claude','5','input') - 1:.0%}")
# break-even N for per-run input (where the search-on line crosses the search-off line), from the two linear fits
be = (csi["a"] - fi["a"]) / (fi["b"] - csi["b"]) if fi["b"] != csi["b"] else float("nan")
F["C_BREAKEVEN"] = f"{be:.0f}"
st_rows = ["| tools | accuracy off | accuracy on | first call off | first call on | per run off | per run on | model calls off | model calls on | ToolSearch calls/run | $/run off | $/run on | wall s off | wall s on |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for v in CSV:
    st_rows.append(f"| {lab(v)} | {cell('claude', v)} | {cell('claude-search', v)} | {k0(x('claude', v, 'first'))} | {k0(x('claude-search', v, 'first'))} | "
                   f"{k0(x('claude', v, 'input'))} | {k0(x('claude-search', v, 'input'))} | {x('claude', v, 'model_calls') or 0:.2f} | {x('claude-search', v, 'model_calls') or 0:.2f} | "
                   f"{x('claude-search', v, 'ts_calls') or 0:.2f} | {x('claude', v, 'cost'):.3f} | {x('claude-search', v, 'cost'):.3f} | {x('claude', v, 'wall'):.1f} | {x('claude-search', v, 'wall'):.1f} |")
for v in CSV:
    tag = "G" if v == "GROUPED" else v
    F[f"C_COSTV_{tag}"] = f"{x('claude', v, 'cost'):.3f}"; F[f"CS_COSTV_{tag}"] = f"{x('claude-search', v, 'cost'):.3f}"
    F[f"C_WALL_{tag}"] = f"{x('claude', v, 'wall'):.1f}"; F[f"CS_WALL_{tag}"] = f"{x('claude-search', v, 'wall'):.1f}"
cw = lambda m, v: st.mean(float(r["cache_write"] or 0) for r in rows if r["model"] == m and r["variant"] == v and r["status"] == "ok")
F.update(C_CW_100=k0(cw("claude", "100")), CS_CW_100=k0(cw("claude-search", "100")))
F["SEARCH_TABLE"] = "\n".join(st_rows)
F["AT100"] = open(os.path.join(H, "at100.md")).read().strip() if os.path.exists(os.path.join(H, "at100.md")) else ""
t = open(os.path.join(H, "report.template.md")).read()
for k, v in F.items():
    t = t.replace("{{" + k + "}}", v)
left = re.findall(r"\{\{[A-Z0-9_]+\}\}", t)
if left: print("unfilled:", left, file=sys.stderr)
open(os.path.join(H, "report.md"), "w").write(t)
print("report.md written")
