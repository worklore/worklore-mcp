#!/usr/bin/env python3
"""Collect runs/<phase>/<model>/<variant>/<task>-r<rep>/row.json into results.csv (one row per run)."""
import csv, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
COLS = ["phase", "model", "model_id", "variant", "n_tools", "task", "kind", "rep", "status", "success", "tools_ok", "args_ok", "strict",
        "n_calls", "n_expected", "wrong_calls", "wrong_ops", "failed_wrong_attempts", "extra_readonly", "repeat_calls", "error_calls", "called_ops",
        "neighbors_present", "input_tokens_total", "input_uncached", "cache_read", "cache_write", "output_tokens", "reasoning_tokens",
        "first_call_input", "model_calls", "cost_usd", "wall_s", "cli_duration_s", "exit_code", "builtin_calls", "builtin_names",
        "schema_reads", "exec_calls", "harness_error"]
rows = []
for p in sorted(glob.glob(os.path.join(HERE, "runs", "*", "*", "*", "*", "row.json"))):
    try:
        rows.append(json.load(open(p)))
    except Exception as e:
        print("bad", p, e, file=sys.stderr)
out = os.path.join(HERE, "results.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, COLS, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        r = dict(r)
        for k in ("wrong_ops", "called_ops", "neighbors_present", "builtin_names"):
            if isinstance(r.get(k), list):
                r[k] = "|".join(map(str, r[k]))
        w.writerow(r)
print(f"{len(rows)} rows -> {out}")
