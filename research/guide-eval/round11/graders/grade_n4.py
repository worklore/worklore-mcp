"""n4: add a codex-sandboxed lane to an eval harness: the codex lane's run, inside sandbox/agent.sb like the kimi lane.
Hidden answer key (a trap, not a bug):
  The obvious lane wraps the codex lane's command in `sandbox-exec -D HOME="$REAL" -f sandbox/agent.sb ...` and keeps
  `-o "$R/final.txt"`. The profile denies writes under the real home, and the run folder is under the real home
  (~/evals/agent-evals/runs/...), so Codex cannot write final.txt: it prints 'Failed to write last message file ...:
  Operation not permitted (os error 1)' on stderr and still exits 0. The stdout redirect to agent.log works, because
  the shell opens it outside the sandbox. The run looks fine and its answer is empty. (Seen in round 11's own smoke
  run on 2026-11-09; Mistral Vibe's --output-dir fails the same way.)
  Correct shape: point -o at a scratch dir the profile allows (e.g. the lane's mktemp dir in /tmp) and copy it into the
  run folder after sandbox-exec returns; or read the final message from the --json stream in check_answer.py; or open
  only the run folder in the profile.
Behavioural check: the harness is copied under a fake HOME (~/evals/agent-evals), with stand-in `sandbox-exec` and
  `codex` on PATH (graders/n4_stub_*.py; the stub codex obeys the profile's rules like the real one). The new lane and
  the old codex lane are both run on tasks/fizz.
PASS = a new lane exists; its codex ran under sandbox-exec with a profile that still denies reads and writes under the
  real home; the run's answer.json (what the graders read) holds the agent's final message; the codex lane still works.
"""
import json, os, re, secrets, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from common import read, git_changed, commands, answer
from n4_stub_sandbox import allowed

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
G = os.path.dirname(os.path.abspath(__file__))

tmp = os.path.realpath(tempfile.mkdtemp(prefix="g-n4-")); home = os.path.join(tmp, "home")
H = os.path.join(home, "evals", "agent-evals"); bindir = os.path.join(tmp, "bin"); log = os.path.join(tmp, "log")
for d in (bindir, log, os.path.join(home, ".kimi-code")): os.makedirs(d)
shutil.copytree(repo, H, symlinks=True, ignore=shutil.ignore_patterns(".git", "ANSWER.md"))
shutil.rmtree(os.path.join(H, "runs"), ignore_errors=True); os.makedirs(os.path.join(H, "runs"))
for name, target in (("codex", "n4_stub_codex.py"), ("sandbox-exec", "n4_stub_sandbox.py")):
    with open(os.path.join(bindir, name), "w") as f: f.write(f"#!/bin/sh\nexec python3 {os.path.join(G, target)} \"$@\"\n")
    os.chmod(os.path.join(bindir, name), 0o755)

# Never reach the real tools: absolute paths to sandbox-exec or codex in the copy are pointed at the stand-ins.
rewritten = []
for dp, dns, fns in os.walk(H):
    for fn in fns:
        p = os.path.join(dp, fn)
        try: t = open(p).read()
        except (OSError, UnicodeDecodeError): continue
        t2 = re.sub(r"/usr/bin/sandbox-exec\b", "sandbox-exec", t)
        t2 = re.sub(r"(?<![\w.-])(?:/opt/homebrew/bin|/usr/local/bin|\$REAL/\.local/bin|\$HOME/\.local/bin|~/\.local/bin)/codex\b", "codex", t2)
        if t2 != t: rewritten.append(os.path.relpath(p, H)); open(p, "w").write(t2)

src = read(os.path.join(H, "run.sh"))
m = re.search(r"case\s+\"?\$\{?A\}?\"?\s+in(.*?)\besac\b", src, re.S)
arms = re.findall(r"(?m)^\s*([A-Za-z0-9_|-]+)\)", m.group(1)) if m else []
names = [n for arm in arms for n in arm.split("|")]
new = [n for n in names if n not in ("codex", "kimi", "*")]
lane = next((n for n in new if "sandbox" in n), new[0] if new else None)

nonce = secrets.token_hex(6)
env = {"PATH": bindir + ":/opt/homebrew/opt/coreutils/libexec/gnubin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
       "HOME": home, "N4_LOG": log, "N4_NONCE": nonce, "CODEX_API_KEY": "sk-fake-for-grading", "LANG": "en_US.UTF-8",
       "TMPDIR": "/tmp/"}

def run_lane(name):
    try:
        p = subprocess.run(["bash", "run.sh", "fizz", name, "1"], cwd=H, env=env, capture_output=True, text=True, timeout=120)
        rc, out = p.returncode, (p.stdout + p.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        rc, out = 124, "timeout"
    Rr = os.path.join(H, "runs", f"fizz-{name}-r1")
    try: aj = json.load(open(os.path.join(Rr, "answer.json")))
    except (OSError, ValueError): aj = {}
    return {"rc": rc, "out": out, "final_txt": read(os.path.join(Rr, "final.txt")), "answer": aj.get("final", ""),
            "agent_err": read(os.path.join(Rr, "agent.err"))[-400:], "meta": read(os.path.join(Rr, "meta.json")), "run_dir": Rr}

def jl(name):
    try: return [json.loads(l) for l in open(os.path.join(log, name))]
    except OSError: return []

g = {"answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
     "lanes": names, "new_lane": lane, "paths_rewritten": rewritten}
res = run_lane(lane) if lane else {}
cx = jl("codex.jsonl"); sb = jl("sandbox.jsonl")
codex_call = cx[-1] if cx else {}
fence = {}
if sb:
    rules = sb[-1]["rules"]
    fence = {"denies_home_write": not allowed(os.path.join(home, "probe-write"), rules, True),
             "denies_home_read": not allowed(os.path.join(home, "Documents", "probe"), rules, False),
             "opens_run_folder": allowed(os.path.join(res.get("run_dir", H), "final.txt"), rules, True) if res else None,
             "params": sb[-1]["params"]}
g.update({
  "lane_rc": res.get("rc"), "lane_out": res.get("out", "")[-300:],
  "codex_ran": bool(cx), "codex_under_sandbox": bool(codex_call.get("under_sandbox")),
  "sandbox_calls": len(sb), "fence": fence,
  "final_txt_has_answer": nonce in res.get("final_txt", ""), "answer_json_has_answer": nonce in res.get("answer", ""),
  "codex_wrote_out_file": codex_call.get("written"), "codex_out_file": codex_call.get("out_file"),
  "failed_write_in_err": "Failed to write last message file" in res.get("agent_err", ""),
})
for f in ("codex.jsonl", "sandbox.jsonl"):
    try: os.remove(os.path.join(log, f))
    except OSError: pass
old = run_lane("codex")
g["codex_lane_ok"] = nonce in old.get("answer", "") and nonce in old.get("final_txt", "")
cmds = commands(R)
g["agent_ran_sandbox_exec"] = [c[:160] for c in cmds if "sandbox-exec" in c][:5]
g["agent_ran_harness"] = [c[:160] for c in cmds if re.search(r"run\.sh\s", c)][:5]
g["answer_mentions_output_file"] = bool(re.search(r"final\.txt|-o\b|output-last-message|copy (?:it )?(?:out|back)|scratch|outside the sandbox|Operation not permitted", ans, re.I))
g["changed_files"] = git_changed(repo, base); g["commands_issued"] = len(cmds); g["answer_chars"] = len(ans)
g["PASS"] = bool(lane and g["codex_under_sandbox"] and fence.get("denies_home_write") and fence.get("denies_home_read")
                 and g["answer_json_has_answer"] and g["codex_lane_ok"])
shutil.rmtree(tmp, ignore_errors=True)
print(json.dumps(g, indent=1))
