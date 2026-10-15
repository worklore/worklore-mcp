#!/usr/bin/env python3
"""Score one run: what text did the agent actually send to check_capability, vs the file on disk?
usage: score.py <run-dir>   -> writes row.json, prints one line.
Ground truth = the tool-call arguments in the agent's own transcript (never its claims)."""
import difflib, hashlib, json, os, re, sys

R = sys.argv[1]
D = os.path.dirname(os.path.abspath(__file__))
meta = json.load(open(os.path.join(R, "meta.json")))
src = open(os.path.join(D, "skills", meta["skill"] + ".md"), encoding="utf-8").read()
srv_hash = lambda t: hashlib.sha256(b"input" + t.encode("utf-8")).hexdigest()  # skill_xray.scan_text(name="input")

objs = []
for fn in ("agent.log", "rollout.jsonl"):
    p = os.path.join(R, fn)
    if os.path.exists(p):
        for line in open(p, encoding="utf-8", errors="replace"):
            try: objs.append(json.loads(line))
            except Exception: pass

def as_args(v):
    if isinstance(v, dict): return v
    if isinstance(v, str) and v.lstrip().startswith("{"):
        try: return json.loads(v)
        except Exception: return None

sent, returned = [], []
def walk(o):
    if isinstance(o, dict):
        if any(isinstance(v, str) and "check_capability" in v for v in o.values()):
            for v in o.values():
                a = as_args(v)
                if a and isinstance(a.get("text"), str): sent.append(a["text"])
                elif a and a.get("url"): sent.append("URL:" + a["url"])
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
    elif isinstance(o, str):
        for m in re.finditer(r'sha256\\?"\s*:\s*\\?"([0-9a-f]{64})', o): returned.append(m.group(1))
for o in objs: walk(o)
# primary ground truth: the proxy's own log of call arguments
cl = os.path.join(R, "calls.jsonl")
if os.path.exists(cl):
    sent = [c["arguments"].get("text") if c["arguments"].get("text") else "URL:" + str(c["arguments"].get("url"))
            for c in map(json.loads, open(cl)) if c.get("name") == "check_capability"]

# de-duplicate (the same call appears in several event types)
seen, calls = set(), []
for t in sent:
    if t not in seen: seen.add(t); calls.append(t)

def classify(t):
    if t.startswith("URL:"): return "url" if re.match(r"URL:https://(github\.com|raw\.githubusercontent\.com)/", t) else "local_path"
    if t == src: return "exact"
    if t.strip() == src.strip(): return "edge_whitespace"
    if [l.rstrip() for l in t.strip().splitlines()] == [l.rstrip() for l in src.strip().splitlines()]: return "line_whitespace"
    if src.startswith(t) or src.strip().startswith(t.strip()): return "truncated"
    return "changed"

row = dict(meta, src_bytes=len(src.encode()), n_calls=len(calls), expected_hash=srv_hash(src),
           returned_hashes=sorted(set(returned)))
if calls:
    t = calls[-1]  # the call whose result the agent reported
    row["class"] = classify(t)
    row["sent_bytes"] = len(t.encode())
    row["hash_matches_file"] = srv_hash(t) == srv_hash(src)
    sm = difflib.SequenceMatcher(None, src.splitlines(), t.splitlines(), autojunk=False)
    row["line_similarity"] = round(sm.ratio(), 4)
    lost = [src.splitlines()[i1:i2] for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("delete", "replace")]
    row["src_lines_lost_or_changed"] = sum(len(x) for x in lost)
    row["diff_sample"] = "\n".join(list(difflib.unified_diff(src.splitlines(), t.splitlines(), lineterm="", n=0))[:30])
    row["all_classes"] = [classify(x) for x in calls]
else:
    row["class"] = "no_call"
# cost and time: what copying (or not copying) the text costs
out_tok = cost = None
for o in objs:
    if o.get("type") == "result" and "usage" in o:          # Claude Code
        out_tok = o["usage"].get("output_tokens"); cost = o.get("total_cost_usd")
    if o.get("event") == "result":                           # Antigravity
        out_tok = (o["result"].get("usage") or {}).get("output_tokens")
    p = o.get("payload") or {}
    if p.get("type") == "token_count" and p.get("info"):     # Codex
        out_tok = ((p["info"].get("total_token_usage") or {}).get("output_tokens"))
row["output_tokens"], row["cost_usd"] = out_tok, cost
row["passed_expected_sha256"] = any("expected_sha256" in (c.get("arguments") or {})
                                    for c in map(json.loads, open(cl))) if os.path.exists(cl) else False
row["status"] = "timeout" if meta["exit_code"] in (124, 137) else "ok"
json.dump(row, open(os.path.join(R, "row.json"), "w"), indent=1)
print(meta["agent"], meta["skill"], f"r{meta['rep']}", row["class"], row.get("sent_bytes"), "/", row["src_bytes"],
      "lost", row.get("src_lines_lost_or_changed"), f"{meta['wall_s']}s")
