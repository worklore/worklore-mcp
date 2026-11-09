#!/usr/bin/env python3
"""Which no-story runs saw the worklore story anyway: python3 exposure.py > exposure.md   (2026-11-09)

Google indexed the two forum-fact stories on 2026-10-21 (s7) and 2026-10-24 (s1), first impressions in Search
Console; round 8 ran from 2026-10-26, so an agent without the story could find it on the web. A run counts as
exposed when its log shows the story page fetched, a story URL in search results, or, for Antigravity, worklore.dev
among the sources of a search summary (Google grounding; those summaries are kept only in Antigravity's local
conversation store, ~/.gemini/antigravity-cli/conversations, which this script reads when it is there).
Limits: Codex's built-in web search logs the query but not its results, so for Codex this is a lower bound.
Two Antigravity runs (r1) have no stored conversation; they searched site:worklore.dev and are counted as exposed.
Claude's search results are logged with their links and never included worklore.dev."""
import glob, json, os, re, subprocess

H = os.path.dirname(os.path.abspath(__file__))
CONV = os.path.expanduser("~/.gemini/antigravity-cli/conversations")
SEVEN = ["claude-opus", "claude-sonnet", "claude-haiku", "codex-sol", "codex-sol-low", "agy-flash-low", "agy-oss"]
KIMI = ["kimi-k28", "kimi-k31"]

def grounding(log):
    m = re.search(r'"conversation_id":"([0-9a-f-]{36})"', log)
    f = m and os.path.join(CONV, m.group(1) + ".db")
    if not f or not os.path.exists(f): return None
    s = subprocess.run(["strings", "-n", "6", f], capture_output=True, text=True).stdout
    return any("[worklore.dev]" in b.split("Sources:", 1)[1][:3000]
               for b in s.split("returned the following summary:")[1:] if "Sources:" in b)

def how(m, log):
    h = []
    if re.search(r'(FetchURL|WebFetch|read_url_content|curl)[^\n]{0,300}worklore\.dev', log): h.append("page fetched")
    if re.search(r'(Title|URL)[^\n]{0,200}worklore\.dev/s/', log): h.append("in search results")
    if m["agent"].startswith("agy"):
        g = grounding(log)
        if g: h.append("in Google grounding sources")
        elif g is None and "worklore.dev" in log: h.append("searched site:worklore.dev (no stored conversation)")
    return h

rows = []
for folder in ["runs", "fresh/runs"]:
    for d in sorted(glob.glob(os.path.join(H, folder, "*"))):
        try: m = json.load(open(os.path.join(d, "meta.json"))); g = json.load(open(os.path.join(d, "grade.json")))
        except Exception: continue
        if "example" in m["arm"] or m.get("rep", 1) < 1 or m.get("limit"): continue
        log = open(os.path.join(d, "agent.log"), errors="ignore").read()
        rows.append((folder, os.path.basename(d), m, bool(g.get("PASS")) and m["exit_code"] == 0, how(m, log)))

print("# No-story runs that saw the worklore story\n")
print(__doc__.split("\n", 2)[2].strip() + "\n")
print("| run | passed | how |\n|---|---|---|")
for folder, name, m, ok, h in rows:
    if h: print(f"| {'fresh/' if folder != 'runs' else ''}{name} | {'yes' if ok else 'no'} | {', '.join(h)} |")
print("\n## Pass rates without a story, all runs and without the exposed ones (round 8 runs only)\n")
print("| agents | arm | all runs | exposed | without exposed |\n|---|---|---|---|---|")
for label, ags in [("seven", SEVEN), ("Kimi", KIMI), ("nine", SEVEN + KIMI)]:
    for arm in ["none-en", "none-ru"]:
        rs = [(ok, h) for f, _, m, ok, h in rows if f == "runs" and m["agent"] in ags and m["arm"] == arm]
        cl = [ok for ok, h in rs if not h]
        p = sum(ok for ok, _ in rs)
        print(f"| {label} | {arm} | {p}/{len(rs)} ({p/len(rs):.1%}) | {len(rs)-len(cl)} | {sum(cl)}/{len(cl)} ({sum(cl)/len(cl):.1%}) |")
print("\n## Per agent, the two stories where it happened\n")
print("| agent | story | none-en | without exposed | none-ru | without exposed |\n|---|---|---|---|---|---|")
for a in SEVEN + KIMI:
    for s in ["s1", "s7"]:
        c = []
        for arm in ["none-en", "none-ru"]:
            rs = [(ok, h) for f, _, m, ok, h in rows if f == "runs" and m["agent"] == a and m["story"] == s and m["arm"] == arm]
            cl = [ok for ok, h in rs if not h]
            c += [f"{sum(ok for ok, _ in rs)}/{len(rs)}", f"{sum(cl)}/{len(cl)}"]
        print(f"| {a} | {s} | " + " | ".join(c) + " |")
