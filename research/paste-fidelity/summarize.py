#!/usr/bin/env python3
"""runs/*/*/row.json -> markdown summary (stdout) + results.csv"""
import csv, glob, json, os
from collections import Counter, defaultdict

D = os.path.dirname(os.path.abspath(__file__))
rows = []
for p in sorted(glob.glob(os.path.join(D, "runs", "*", "*", "*", "row.json"))):
    r = json.load(open(p)); r["phase"] = p.split(os.sep)[-4]; rows.append(r)
import statistics
med = lambda xs: statistics.median(xs) if xs else None
COLS = ["phase", "agent", "skill", "rep", "src_bytes", "sent_bytes", "class", "hash_matches_file", "line_similarity",
        "src_lines_lost_or_changed", "n_calls", "wall_s", "output_tokens", "cost_usd", "passed_expected_sha256", "exit_code", "status"]
with open(os.path.join(D, "results.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, COLS, extrasaction="ignore"); w.writeheader(); [w.writerow(r) for r in rows]

AG = {"claude": "Claude Code · Opus 5.5", "codex": "Codex CLI · default", "gemini": "Antigravity · Gemini 3.8 Flash high"}
print("# Paste-hash test: does the text an agent sends to check_capability match the file?\n")
print(f"{len(rows)} runs. `exact` = byte-identical, so the returned sha256 describes the real file.\n")
print("| phase | agent | runs | exact text | passed the url | whitespace only | truncated | changed | unusable path / no call | sent expected_sha256 | 75 KB file: median output tokens / wall s / $ |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for ph in ("before", "after-file", "after-url"):
  for a in AG:
    rs = [r for r in rows if r["agent"] == a and r["phase"] == ph]
    if not rs: continue
    c = Counter(r["class"] for r in rs)
    big = [r for r in rs if r["skill"] == "siege"]
    tok = med([r["output_tokens"] for r in big if r.get("output_tokens") is not None])
    wall = med([r["wall_s"] for r in big]); cost = med([r["cost_usd"] for r in big if r.get("cost_usd")])
    print(f"| {ph} | {AG[a]} | {len(rs)} | {c['exact']} | {c['url']} | {c['edge_whitespace'] + c['line_whitespace']} | {c['truncated']} | "
          f"{c['changed']} | {c['local_path'] + c['no_call']} | {sum(bool(r.get('passed_expected_sha256')) for r in rs)} | "
          f"{tok if tok is not None else '–'} / {wall} / {'%.2f' % cost if cost else '–'} |")
print("\n## By file size (exact / runs, all agents)\n")
print("| skill | bytes | " + " | ".join(AG) + " |"); print("|---|---|" + "---|" * len(AG))
by = defaultdict(list)
for r in rows:
    if r["phase"] == "before": by[(r["skill"], r["agent"])].append(r)
for s, b in sorted({(r["skill"], r["src_bytes"]) for r in rows}, key=lambda x: x[1]):
    cells = []
    for a in AG:
        rs = by[(s, a)]
        cells.append(f"{sum(r['class'] == 'exact' for r in rs)}/{len(rs)}" if rs else "–")
    print(f"| {s} | {b:,} | " + " | ".join(cells) + " |")
print("\n## Every non-exact run\n")
for r in rows:
    if r["class"] not in ("exact", "url", "local_path"):
        print(f"### {r['phase']} · {r['agent']} · {r['skill']} r{r['rep']} — {r['class']} "
              f"(sent {r.get('sent_bytes')} of {r['src_bytes']} bytes, {r.get('src_lines_lost_or_changed')} source lines lost/changed)\n")
        if r.get("diff_sample"): print("```diff\n" + r["diff_sample"][:1500] + "\n```\n")
