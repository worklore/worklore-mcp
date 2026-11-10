"""The final answer of a run, as the graders read it: final.txt (Codex lanes), else the last assistant message in
the Kimi stream-json log. usage: check_answer.py <run folder>  ->  {"final": "...", "source": "..."}"""
import json, os, sys

R = sys.argv[1]
def read(p):
    try: return open(p, errors="replace").read()
    except OSError: return ""

final, source = read(os.path.join(R, "final.txt")), "final.txt"
lane = json.loads(read(os.path.join(R, "meta.json")) or "{}").get("lane", "")
if not final.strip() and lane.startswith("kimi"):
    source = "agent.log"
    for line in reversed(read(os.path.join(R, "agent.log")).splitlines()):
        try: d = json.loads(line)
        except ValueError: continue
        if d.get("role") == "assistant" and isinstance(d.get("content"), str) and d["content"].strip():
            final = d["content"]; break
if not final.strip() and lane.startswith("codex"):
    source = "agent.log"
    for line in read(os.path.join(R, "agent.log")).splitlines():
        try: d = json.loads(line)
        except ValueError: continue
        it = d.get("item") or {}
        if d.get("type") == "item.completed" and it.get("type") == "agent_message": final = it.get("text", "")
print(json.dumps({"final": final, "source": source if final.strip() else "none"}))
