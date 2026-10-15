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
    wd = read(os.path.join(R, "workdir")).strip()
    inside = [repo] + ([wd, "/private" + wd] if wd else [])
    hits = set()
    for m in re.finditer(r"(/(?:Users|private|tmp|etc|var|opt|home)/[A-Za-z0-9_./~-]+)", txt):
        p = m.group(1).rstrip(".")
        if any(p.startswith(i) for i in inside) or p.startswith("/opt/homebrew") or "/.local/bin" in p:
            continue
        hits.add(p)
    return sorted(hits)[:40]

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
