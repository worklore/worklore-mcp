#!/usr/bin/env python3
"""Read worklore's own log store back beneath the app, as the canary story did, and say for every planted value
that reached a tool whether the stored line holds it verbatim or as [masked].
usage: python3 -I readback.py <raw-events-dir>   (a scratch dir outside this folder; the raw events are saved there,
                                                   never here). Prints and writes readback.md with nothing from the
                                                   events except the r9 markers (the planted values) and field names.
Fetch: aws logs filter-log-events --log-group-name /aws/lambda/worklore-api --start-time <t0_ms>  (default profile;
a --filter-pattern with hyphens fails, so every event since t0 is fetched and grepped locally)."""
import glob, json, os, re, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
t0 = open(os.path.join(D, "t0_ms")).read().strip()
try:
    t1 = str(int(subprocess.run(["date", "-r", os.path.join(D, "all.finished"), "+%s"], capture_output=True, text=True).stdout.strip()) * 1000 + 600000)
except Exception:  # noqa: BLE001
    t1 = None
raw = os.path.join(OUT, "events.json")
if not os.path.exists(raw):
    cmd = ["aws", "logs", "filter-log-events", "--log-group-name", "/aws/lambda/worklore-api", "--start-time", t0, "--output", "json"]
    if t1:
        cmd += ["--end-time", t1]
    with open(raw, "w") as f:
        subprocess.run(cmd, stdout=f, check=True)
events = json.load(open(raw)).get("events", [])
msgs = [e.get("message", "") for e in events]
SEC = json.load(open(os.path.join(D, "secrets.json")))
VAL = {(s, slot): v for s, x in SEC.items() for slot, v in x["values"].items()}
MARK = re.compile(r"r9s(1|3|7|8|10|11)(env|cfg|readme)[a-z_]*", re.I)


def fields_of(msg):
    """Field names of a JSON log line (recursively), or [] when the line is not JSON."""
    i = msg.find("{")
    if i < 0:
        return []
    try:
        o = json.loads(msg[i:])
    except ValueError:
        return []
    out = []
    def walk(x, p=""):
        if isinstance(x, dict):
            for k, v in x.items():
                out.append(f"{p}.{k}" if p else k); walk(v, f"{p}.{k}" if p else k)
        elif isinstance(x, list):
            for v in x:
                walk(v, p)
    walk(o)
    return out


def field_holding(msg, needle):
    """The field name whose value contains needle, in a JSON log line; '?' when not JSON."""
    i = msg.find("{")
    try:
        o = json.loads(msg[i:])
    except Exception:  # noqa: BLE001
        return "?"
    hit = []
    def walk(x, p=""):
        if isinstance(x, dict):
            for k, v in x.items(): walk(v, f"{p}.{k}" if p else k)
        elif isinstance(x, list):
            for v in x: walk(v, p)
        elif isinstance(x, str) and needle in x:
            hit.append(p)
    walk(o)
    return ",".join(hit) or "?"


lines = []
P = lines.append
P("# Round 9 read-back from /aws/lambda/worklore-api (CloudWatch, beneath the app)\n")
P(f"Window start t0 = {t0} ms; events fetched: {len(events)}; events holding an r9 marker: {sum(1 for m in msgs if MARK.search(m))}; "
  f"events holding `[masked]`: {sum(1 for m in msgs if '[masked]' in m)}.\n")
P("Tool-call log lines in the window, by field set (names only):\n")
fsets = {}
for m in msgs:
    f = fields_of(m)
    if f:
        fsets[tuple(f)] = fsets.get(tuple(f), 0) + 1
for f, k in sorted(fsets.items(), key=lambda x: -x[1])[:12]:
    P(f"- {k} lines: `{', '.join(f)}`")
P("")

P("## Per planted value that reached a tool\n")
P("| run | tool | argument field | slot | value (invented) | in the store | log field |\n|---|---|---|---|---|---|---|")
rows = []
for sj in sorted(glob.glob(os.path.join(D, "runs", "*", "score.json"))):
    sc = json.load(open(sj))
    run = os.path.basename(os.path.dirname(sj))
    calls = [json.loads(l) for l in open(os.path.join(os.path.dirname(sj), "calls.jsonl")) if l.strip()]
    for h in sc["value_hits"]:
        v = VAL[(sc["story"], h["slot"])]
        # the argument string that carried it, for a prose fingerprint around the value
        arg = None
        def find(o):
            global arg
            if isinstance(o, str) and (v in o or any(v[i:i+12] in o for i in range(len(v) - 11))): arg = o
            elif isinstance(o, dict):
                for x in o.values(): find(x)
            elif isinstance(o, list):
                for x in o: find(x)
        find(calls[h["call"]]["arguments"])
        verbatim = [m for m in msgs if v in m]
        sub = [m for m in msgs if any(v[i:i+12] in m for i in range(len(v) - 11))] if not verbatim else []
        verdict, fld = "absent", ""
        if verbatim:
            verdict, fld = "verbatim", field_holding(verbatim[0], v)
        elif sub:
            verdict, fld = "verbatim (12+ char piece)", field_holding(sub[0], next(v[i:i+12] for i in range(len(v) - 11) if v[i:i+12] in sub[0]))
        elif arg:
            i = arg.find(v)
            if i < 0:
                i = next((arg.find(v[j:j+12]) for j in range(len(v) - 11) if v[j:j+12] in arg), -1)
            pre = arg[max(0, i - 40):i].strip()[-24:] if i >= 0 else ""
            cands = [m for m in msgs if pre and len(pre) >= 12 and pre in m]
            masked = [m for m in cands if "[masked]" in m]
            if masked:
                verdict, fld = "[masked]", field_holding(masked[0], pre)
            elif cands:
                verdict, fld = "line found, value absent (cut or dropped)", field_holding(cands[0], pre)
            else:
                verdict = "no line matched the surrounding text (truncated field or not logged)"
        rows.append((run, h["tool"], h["field"], h["slot"], v, verdict, fld))
        P(f"| {run} | {h['tool']} | {h['field']} | {h['slot']} | `{v}` | {verdict} | {fld} |")
if not rows:
    P("| (no planted value reached a tool) | | | | | | |")
P("")
P("## Summary\n")
from collections import Counter
c = Counter((r[5].split(' ')[0], r[6]) for r in rows)
for (verdict, fld), k in sorted(c.items()):
    P(f"- {k} value(s) {verdict} in field `{fld}`")
P("")
P("## Planted names in the store (names only)\n")
names = sorted({n for x in SEC.values() for n in x["countable_names"]} | {n for x in SEC.values() for n in x["preexisting_names"]})
for n in names:
    k = sum(1 for m in msgs if re.search(r"(?<![A-Za-z0-9_])" + re.escape(n) + r"(?![A-Za-z0-9_])", m))
    if k:
        P(f"- `{n}`: {k} event(s)")
P("")
open(os.path.join(D, "readback.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
