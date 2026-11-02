import json, os, re, subprocess, sys

def read(p):
    try:
        with open(p, errors="replace") as f:
            return f.read()
    except OSError:
        return ""

def run_text(R):
    """All agent output (tool calls + messages), JSON-unescaped best effort."""
    raw = read(os.path.join(R, "agent.log")) + "\n" + read(os.path.join(R, "agent.err"))
    try:
        un = raw.encode().decode("unicode_escape", errors="ignore")
    except Exception:
        un = raw
    return raw + "\n" + un

def outside_paths(R):
    """Absolute paths in the log that are outside the run's repo (best effort)."""
    txt = run_text(R)
    repo = os.path.join(R, "repo")
    hits = set()
    for m in re.finditer(r"(/(?:Users|private|tmp|etc|var|opt|home)/[A-Za-z0-9_./~-]+)", txt):
        p = m.group(1).rstrip(".")
        if p.startswith(repo) or p.startswith("/opt/homebrew") or "/.local/bin" in p:
            continue
        if "/story-eval/" in p and "/runs/" not in p and "/graders" not in p and "/fixtures" not in p and "/stories" not in p:
            continue
        hits.add(p)
    return sorted(hits)[:25]

def git_changed(repo, base):
    out = subprocess.run(["git", "diff", "--name-only", base], cwd=repo, capture_output=True, text=True).stdout.split()
    un = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo, capture_output=True, text=True).stdout.split()
    return sorted(set(out) | set(un))

def commands(R):
    """Shell commands the agent actually issued (from structured logs)."""
    out = []
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ("command", "CommandLine", "cmd") and isinstance(v, str):
                    out.append(v)
                elif k in ("command", "cmd") and isinstance(v, list):
                    out.append(" ".join(map(str, v)))
                else:
                    walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    for line in read(os.path.join(R, "agent.log")).splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                walk(json.loads(line))
            except Exception:
                pass
    return list(dict.fromkeys(out))

def final_response(R):
    """The agent's final message: Codex final.txt, Antigravity/Claude stream-json result line."""
    t = read(os.path.join(R, "final.txt"))
    if t.strip(): return t
    for line in reversed(read(os.path.join(R, "agent.log")).splitlines()):
        if '"result"' in line and line.startswith("{"):
            try:
                d = json.loads(line)
                r = d.get("result")
                if isinstance(r, dict) and r.get("response"): return r["response"]
                if isinstance(r, str): return r
            except Exception:
                pass
    return ""

def answer(R):
    """ANSWER.md from the repo; else the same file Antigravity wrote into its own brain dir; else the final message."""
    a = read(os.path.join(R, "repo", "ANSWER.md"))
    if a.strip(): return a
    m = re.search(r'"conversation_id":\s*"([0-9a-f-]{36})"', read(os.path.join(R, "agent.log")))
    if m:
        b = read(os.path.expanduser(f"~/.gemini/antigravity-cli/brain/{m.group(1)}/ANSWER.md"))
        if b.strip(): return b
    return final_response(R)
