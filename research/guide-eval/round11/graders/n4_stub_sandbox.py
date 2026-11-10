"""A stand-in `sandbox-exec` for grade_n4.py. It reads the SBPL profile (-f file or -p string, -D NAME=value params),
keeps its file-read/file-write rules, logs the invocation to $N4_LOG/sandbox.jsonl, and runs the command with the
rules in SANDBOX_STUB_RULES, so the stub `codex` behaves as Codex does under the real sandbox. It enforces nothing
itself: only the stub tools check the rules. Shared helpers (rule parsing and matching) are imported by the stubs."""
import json, os, re, sys

def tokens(s):
    s = re.sub(r";[^\n]*", "", s); out = []; i = 0
    while i < len(s):
        c = s[i]
        if c.isspace(): i += 1; continue
        if c in "()": out.append(c); i += 1; continue
        if c == '"' or (c == "#" and s[i + 1:i + 2] == '"'):
            j = i + (2 if c == "#" else 1); buf = ""
            while j < len(s) and s[j] != '"':
                if s[j] == "\\": buf += s[j + 1]; j += 2; continue
                buf += s[j]; j += 1
            out.append(("str", buf)); i = j + 1; continue
        j = i
        while j < len(s) and not s[j].isspace() and s[j] not in "()": j += 1
        out.append(s[i:j]); i = j
    return out

def parse(toks):
    stack = [[]]
    for t in toks:
        if t == "(": stack.append([])
        elif t == ")":
            x = stack.pop(); stack[-1].append(x)
        else: stack[-1].append(t)
    return stack[0]

def ev(x, params):
    if isinstance(x, tuple): return x[1]
    if isinstance(x, list) and x:
        if x[0] == "param": return params.get(ev(x[1], params), "")
        if x[0] == "string-append": return "".join(ev(y, params) for y in x[1:])
    return str(x)

def real(p):
    return os.path.realpath(os.path.expanduser(p))

def rules_of(text, params):
    rules = []
    for form in parse(tokens(text)):
        if not isinstance(form, list) or form[:1] not in (["allow"], ["deny"]): continue
        action, op = form[0], form[1]
        if not isinstance(op, str) or not op.startswith("file-"): continue
        for f in form[2:]:
            if isinstance(f, list) and f and f[0] in ("subpath", "literal", "prefix", "regex"):
                val = ev(f[1], params)
                rules.append({"action": action, "op": op, "kind": f[0], "path": real(val) if f[0] != "regex" else val})
            elif isinstance(f, list) and f and f[0] == "require-any":
                for g in f[1:]:
                    if isinstance(g, list) and g and g[0] in ("subpath", "literal", "prefix"):
                        rules.append({"action": action, "op": op, "kind": g[0], "path": real(ev(g[1], params))})
        if len(form) == 2:
            rules.append({"action": action, "op": op, "kind": "all", "path": "/"})
    return rules

def allowed(path, rules, write):
    p = real(path); result = True
    ops = ("file-write*", "file-write-data", "file-write-create", "file*") if write else ("file-read*", "file-read-data", "file*")
    for r in rules:
        if r["op"] not in ops: continue
        k, q = r["kind"], r["path"]
        hit = (k == "all" or (k == "subpath" and (p == q or p.startswith(q.rstrip("/") + "/")))
               or (k == "literal" and p == q) or (k == "prefix" and p.startswith(q))
               or (k == "regex" and re.search(q, p) is not None))
        if hit: result = (r["action"] == "allow")
    return result

if __name__ == "__main__":
    a = sys.argv[1:]; params = {}; prof = None; i = 0
    while i < len(a):
        x = a[i]
        if x == "-D": k, _, v = a[i + 1].partition("="); params[k] = v; i += 2; continue
        if x.startswith("-D") and "=" in x: k, _, v = x[2:].partition("="); params[k] = v; i += 1; continue
        if x == "-f": prof = open(a[i + 1]).read(); pf = a[i + 1]; i += 2; continue
        if x == "-p": prof = a[i + 1]; pf = "<inline>"; i += 2; continue
        if x == "-n": prof = ""; pf = "named:" + a[i + 1]; i += 2; continue
        break
    cmd = a[i:]
    if prof is None or not cmd:
        sys.stderr.write("usage: sandbox-exec [-f profile-file] [-n profile-name] [-p profile-string] [-D key=value ...] command [arguments ...]\n"); sys.exit(64)
    rules = rules_of(prof, params)
    log = os.environ.get("N4_LOG")
    if log:
        with open(os.path.join(log, "sandbox.jsonl"), "a") as f:
            f.write(json.dumps({"profile": pf, "params": params, "rules": rules, "cmd": cmd, "cwd": os.getcwd()}) + "\n")
    os.environ["SANDBOX_STUB_RULES"] = json.dumps(rules)
    try:
        os.execvp(cmd[0], cmd)
    except OSError as e:
        sys.stderr.write(f"sandbox-exec: execvp() of '{cmd[0]}' failed: {e.strerror}\n"); sys.exit(71)
