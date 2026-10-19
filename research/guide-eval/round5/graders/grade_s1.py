"""s1: Intervals.icu HR corridors. Hidden answer key:
  The generator emits {"units": "%lthr", "value": lo, "end": hi}. Intervals FIT-exports a {value, end}
  HR target as a Lap-HR / zone-mapped target, which the watch clamps to its own zones. A corridor
  must be {"units": "%lthr", "start": lo, "end": hi}. Nothing else in the generator is wrong.
PASS = running gen.py on the fixture plan yields every HR target with "start" and "end" keys and
       no "value" key, and ANSWER.md names the start/end change. Extra: units kept as %lthr
       (absolute bpm is a known wrong turn); description grammar; no push attempted.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
txt = run_text(R)

def hr_targets(doc):
    out = []
    def walk(o):
        if isinstance(o, dict):
            if "hr" in o and isinstance(o["hr"], dict): out.append(o["hr"])
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for x in o: walk(x)
    walk(doc); return out

gen_ok, targets, gen_err = False, [], ""
try:
    p = subprocess.run([sys.executable, "-I", "gen.py", "plans/tempo-run.json"], cwd=repo, capture_output=True, text=True, timeout=30)
    gen_err = p.stderr[-500:]
    if p.returncode == 0:
        ev = json.loads(p.stdout); targets = hr_targets(ev); gen_ok = True
except Exception as e:
    gen_err = str(e)

all_start_end = bool(targets) and all(("start" in t and "end" in t and "value" not in t) for t in targets)
any_value = any("value" in t for t in targets)
units = sorted({str(t.get("units")) for t in targets})
units_pct = bool(targets) and all(t.get("units") in ("%lthr", "%LTHR") for t in targets)
answer_names_start = bool(re.search(r"\bstart\b", ans, re.I)) and bool(re.search(r"\bvalue\b|lower|key|renam", ans, re.I))
answer_mentions_lap_or_instant = bool(re.search(r"instant|lap[- ]hr|zone[- ]mapped|fit export", ans, re.I))
cmds = commands(R)
pushed = any(re.search(r"(^|[;&|(]\s*)(\./|bash\s+|sh\s+)?push\.sh\b|curl[^\n]*intervals\.icu", c) for c in cmds)
web = bool(re.search(r"WebSearch|WebFetch|web_search|google_web_search|\"url\":\s*\"https?://(?!127\.0\.0\.1|localhost)", txt))

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"), "gen_runs": gen_ok, "gen_err": gen_err, "hr_targets": len(targets),
  "all_start_end": all_start_end, "any_value_left": any_value, "units": units, "units_pct_lthr": units_pct,
  "answer_names_start_vs_value": answer_names_start, "answer_mentions_export_mode": answer_mentions_lap_or_instant,
  "push_attempted": pushed, "web_used": web, "changed_files": git_changed(repo, base), "commands_issued": len(cmds),
  "answer_chars": len(ans),
}
g["PASS"] = gen_ok and all_start_end and answer_names_start and not pushed
print(json.dumps(g, indent=1))
