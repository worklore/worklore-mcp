#!/usr/bin/env python3
"""Round 5 tables from runs/*/grade.json + meta.json -> stdout (markdown)."""
import glob, json, os, collections
H = os.path.dirname(os.path.abspath(__file__))
AG = ["claude-opus", "claude-sonnet", "claude-haiku", "codex-sol", "codex-sol-low", "agy-argon-high", "agy-argon-low", "agy-flash-low", "agy-oss"]
ARMS = ["none", "follow", "example", "notes"]
STORY = {"s1": "HR corridors (niche fact)", "s2": "PostHogWidget (fact in docs)", "s3": "silent launchd job (two traps)",
         "s4": "Cache-Control deploy (trap to fall into)", "s5": "Soft 404 / robots.txt (derivable)", "s6": "MCP checkup (method)"}
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
    if m["exit_code"] == 3: return "q"      # Antigravity quota exhausted, not run
    if m["exit_code"] == 124: return "t"    # 20-minute timeout, counted as fail
    if m["exit_code"] not in (0,): return f"err{m['exit_code']}"
    return "**P**" if g.get("PASS") else "f"

print("## PASS grid (P = pass, f = fail, t = timeout at 20 min (fail), q = Antigravity quota exhausted (not run), · = not run)\n")
for s in ["s1", "s2", "s3", "s4", "s5", "s6"]:
    print(f"### {s}: {STORY[s]}\n")
    print("| agent | " + " | ".join(ARMS) + " | time none/follow/example/notes |")
    print("|---|" + "---|" * (len(ARMS) + 1))
    for a in AG:
        times = "/".join(str(runs[(s, a, arm)][0]["wall_s"]) if (s, a, arm) in runs else "·" for arm in ARMS)
        print(f"| {a} | " + " | ".join(cell(s, a, arm) for arm in ARMS) + f" | {times} |")
    print()

print("## Totals per story and arm (passes / runs)\n")
print("| story | " + " | ".join(ARMS) + " |")
print("|---|" + "---|" * len(ARMS))
for s in ["s1", "s2", "s3", "s4", "s5", "s6"]:
    row = []
    for arm in ARMS:
        xs = [g.get("PASS") for (ss, a, ar), (m, g) in runs.items() if ss == s and ar == arm and m["exit_code"] != 3]
        row.append(f"{sum(bool(x) for x in xs)}/{len(xs)}" if xs else "·")
    print(f"| {s} {STORY[s]} | " + " | ".join(row) + " |")
print()
print("## Totals per agent and arm\n")
print("| agent | " + " | ".join(ARMS) + " |")
print("|---|" + "---|" * len(ARMS))
for a in AG:
    row = []
    for arm in ARMS:
        xs = [g.get("PASS") for (ss, aa, ar), (m, g) in runs.items() if aa == a and ar == arm and m["exit_code"] != 3]
        row.append(f"{sum(bool(x) for x in xs)}/{len(xs)}" if xs else "·")
    print(f"| {a} | " + " | ".join(row) + " |")
print()

# per-story detail columns
DETAIL = {
 "s1": ["all_start_end", "units", "answer_mentions_export_mode", "web_used", "push_attempted"],
 "s2": ["router_wrapped", "legacy_still_wrapped", "answer_explains_frames", "comment_left", "web_used"],
 "s3": ["bug1_named", "bug2_named", "bug1_fixed", "bug2_fixed", "cites_runs_or_exit_code", "explains_notifier_downstream"],
 "s4": ["cache_control_set", "trap_hits", "content_type_explicit", "tiered_ttls", "retags_existing_objects", "answer_mentions_content_type_or_trap"],
 "s5": ["cause_named", "public_reads_allowed", "private_still_blocked", "admin_still_blocked", "dates_noted", "recrawl_named", "web_used"],
 "s6": ["P1_resources_401", "P2_refusal_as_protocol_error", "P3_vacuous_outputSchema", "false_alarms", "add_note_called_with_token", "story_links", "server_changed"],
}
print("## Detail per run\n")
for s in ["s1", "s2", "s3", "s4", "s5", "s6"]:
    cols = DETAIL[s]
    print(f"### {s}\n")
    print("| agent | arm | PASS | " + " | ".join(cols) + " | chars | s |")
    print("|---|---|---|" + "---|" * (len(cols) + 2))
    for a in AG:
        for arm in ARMS:
            r = runs.get((s, a, arm))
            if not r: continue
            m, g = r
            def fmt(v):
                if isinstance(v, bool): return "Y" if v else "n"
                if isinstance(v, list): return str(len(v)) if v else "-"
                return str(v)
            print(f"| {a} | {arm} | {'P' if g.get('PASS') else 'f'} | " + " | ".join(fmt(g.get(c)) for c in cols) + f" | {g.get('answer_chars')} | {m['wall_s']} |")
    print()
