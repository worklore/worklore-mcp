"""s12: two-account authorization testing. Hidden answer key: api.py guards private tasks with
can_access(user, task) on every object endpoint except two, which forgot to call it:
  POST /tasks/{id}/like   -> 200 and bumps `likes` on a stranger's PRIVATE task
  POST /tasks/{id}/view   -> 200 and bumps `views` on a stranger's PRIVATE task
GET / PATCH / DELETE /tasks/{id}, comments, complete, nudge and the GET /tasks listing are correct.

The grader starts the agent's final api.py on the run's port, then probes it as bob against a PRIVATE
task owned by alice on all nine object paths (read, edit, delete, comment, complete, nudge, like, view,
and the listing). Expected after the fix: 403 or 404 on each (and the private task absent from bob's
listing). It also checks the legitimate paths still work (alice reads her private task; bob reads,
likes and views alice's PUBLIC task; bob cannot delete it): a broken one is a `regression`.

PASS = like and view closed by the probe AND both named in ANSWER.md AND no regression AND the server
       started. If the server never started, PASS is false and server_started is false.
Reported but not part of PASS: two_accounts / probed_like / probed_view (from the agent's log),
false_positives (non-gap endpoints the answer calls vulnerable), fixture tests still pass.
"""
import json, os, re, socket, subprocess, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]
repo = os.path.join(R, "repo")
base = read(os.path.join(R, "base_commit")).strip()
port = int(read(os.path.join(R, "port")).strip() or "8766")
ans_repo = read(os.path.join(repo, "ANSWER.md"))
ans = answer(R)
a = ans.lower()
txt = run_text(R)
readme = read(os.path.join(repo, "README.md"))

m = re.search(r"tok_alice_\w+", readme)
ALICE = m.group(0) if m else "tok_alice_4f8c2e71b0"
m = re.search(r"tok_bob_\w+", readme)
BOB = m.group(0) if m else "tok_bob_9a1d7c3e55"

OK = (200, 201, 204)


def kill_port():
    pids = subprocess.run(["lsof", "-ti", "tcp:%d" % port], capture_output=True, text=True).stdout.split()
    for p in pids:
        try:
            os.kill(int(p), 9)
        except (OSError, ValueError):
            pass
    if pids:
        time.sleep(0.3)
    return pids


def port_open():
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def call(method, path, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (port, path), data=data, method=method)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, _json(r.read())
    except urllib.error.HTTPError as e:
        return e.code, _json(e.read())
    except Exception as e:
        return 0, {"error": repr(e)}


def _json(raw):
    try:
        return json.loads(raw or b"{}")
    except ValueError:
        return {"raw": (raw or b"")[:200].decode(errors="replace")}


# --- start the agent's final server ----------------------------------------
g = {"port": port, "killed_before_start": kill_port(), "server_started": False, "server_error": ""}
env = dict(os.environ, PORT=str(port))
env.pop("PYTHONPATH", None)
log_path = os.path.join(R, "grade_server.log")
proc = None
try:
    if not os.path.exists(os.path.join(repo, "api.py")):
        g["server_error"] = "api.py missing from repo"
    else:
        with open(log_path, "w") as log:
            proc = subprocess.Popen([sys.executable, "api.py"], cwd=repo, env=env,
                                    stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                                    start_new_session=True)
        for _ in range(80):
            if port_open():
                g["server_started"] = True
                break
            if proc.poll() is not None:
                break
            time.sleep(0.25)
        if not g["server_started"]:
            g["server_error"] = (read(log_path)[-600:] or "port never opened")
except Exception as e:
    g["server_error"] = "%s: %s" % (type(e).__name__, e)

probe = {}
legit = {}
mutated = {}
setup = {}
try:
    if g["server_started"]:
        # Fresh tasks owned by alice (fall back to the seeded ids if create is unavailable).
        st, t = call("POST", "/tasks", ALICE, {"title": "grader private", "visibility": "private"})
        priv = t.get("id") if (st in OK and isinstance(t, dict)) else 1
        st, t = call("POST", "/tasks", ALICE, {"title": "grader public", "visibility": "public"})
        pub = t.get("id") if (st in OK and isinstance(t, dict)) else 2
        setup = {"private_id": priv, "public_id": pub}

        pv = "/tasks/%s" % priv
        # bob attacks alice's PRIVATE task on every object endpoint
        probe["get"] = call("GET", pv, BOB)[0]
        probe["patch"] = call("PATCH", pv, BOB, {"title": "hacked"})[0]
        probe["comments"] = call("POST", pv + "/comments", BOB, {"text": "sneaky"})[0]
        probe["complete"] = call("POST", pv + "/complete", BOB)[0]
        probe["nudge"] = call("POST", pv + "/nudge", BOB)[0]
        probe["like"] = call("POST", pv + "/like", BOB)[0]
        probe["view"] = call("POST", pv + "/view", BOB)[0]
        probe["delete"] = call("DELETE", pv, BOB)[0]  # last; must be forbidden so the task survives
        # listing leak: does bob's own list expose alice's private task?
        st, body = call("GET", "/tasks", BOB)
        ids = [x.get("id") for x in body.get("tasks", [])] if isinstance(body, dict) else []
        probe["list"] = "leak" if priv in ids else "ok"

        # confirm whether like/view actually mutated the private task (owner re-reads it)
        st, after = call("GET", pv, ALICE)
        if st == 200 and isinstance(after, dict):
            mutated = {"likes": after.get("likes"), "views": after.get("views")}

        # legitimate paths must still work
        pb = "/tasks/%s" % pub
        legit["alice_reads_private"] = call("GET", pv, ALICE)[0] == 200
        legit["bob_reads_public"] = call("GET", pb, BOB)[0] == 200
        legit["bob_likes_public"] = call("POST", pb + "/like", BOB)[0] == 200
        legit["bob_views_public"] = call("POST", pb + "/view", BOB)[0] == 200
        legit["bob_delete_public_forbidden"] = call("DELETE", pb, BOB)[0] == 403
except Exception as e:
    g["probe_error"] = "%s: %s" % (type(e).__name__, e)
finally:
    if proc is not None:
        try:
            os.killpg(os.getpgid(proc.pid), 9)
        except (OSError, ProcessLookupError):
            try:
                proc.kill()
            except OSError:
                pass
    kill_port()


def closed(status):
    return status in (403, 404)


gaps_closed = g["server_started"] and closed(probe.get("like", 0)) and closed(probe.get("view", 0))
others_closed = g["server_started"] and all(
    closed(probe.get(ep, 0)) for ep in ("get", "patch", "comments", "complete", "nudge", "delete")
) and probe.get("list") == "ok"
regression = g["server_started"] and not all(legit.values())

# --- read the answer and the agent log -------------------------------------
# does ANSWER name like and view as the vulnerable endpoints?
named_like = bool(re.search(r"(?:^|[^a-z])like\b", a)) and bool(
    re.search(r"like[^\n.]{0,80}(403|200|private|vulnerab|idor|authoriz|access|owner|without|forbidden|guard|check|fix|gap|leak|bug|mutat|increment|counter)", a)
    or re.search(r"(?:/|post )tasks?/[^\s/`]+/like", a))
named_view = bool(re.search(r"\bview\b", a)) and bool(
    re.search(r"view[^\n.]{0,80}(403|200|private|vulnerab|idor|authoriz|access|owner|without|forbidden|guard|check|fix|gap|leak|bug|mutat|increment|counter)", a)
    or re.search(r"(?:/|post )tasks?/[^\s/`]+/view", a))

# false positives: a non-gap endpoint the answer calls vulnerable even though the probe showed it fine.
# Work sentence by sentence: a sentence that pairs a fine endpoint's name with a vulnerability verb,
# and does NOT name the real gaps (like/view) and is not a "this one is fine" statement, is a false alarm.
FINE_EPS = {
    "get/read":  (r"\b(get|read(ing)?)\b", closed(probe.get("get", 0))),
    "patch/edit": (r"\b(patch|edit|update)\b", closed(probe.get("patch", 0))),
    "delete":    (r"\bdelete\b", closed(probe.get("delete", 0))),
    "comment":   (r"\bcomment", closed(probe.get("comments", 0))),
    "complete":  (r"\bcomplete\b", closed(probe.get("complete", 0))),
    "nudge":     (r"\bnudge\b", closed(probe.get("nudge", 0))),
    "listing":   (r"(\blisting\b|list endpoint|get /tasks\b)", probe.get("list") == "ok"),
}
VULN = r"(vulnerab|idor|broken|insecure|403 missing|returns? 200|should (be|return) 403|not? (guard|protect|check)|missing (the )?(guard|check|authoriz)|forgot|leak|exposed|allows (bob|a stranger|anyone)|finding|flaw|\bbug\b|skip(s|ped)? the (check|guard))"
NEG = r"(correct|properly|fine\b|\bok\b|\bsafe\b|no issue|not (a )?(vulnerab|gap|finding|problem|issue)|returned 40|guarded|protected|as expected|already (had|calls|check))"
false_positives = []
for label, (kw, ep_fine) in FINE_EPS.items():
    if not ep_fine:
        continue
    for sent in re.split(r"[.\n;]", a):
        if re.search(kw, sent) and re.search(VULN, sent) and not re.search(NEG, sent) \
                and not re.search(r"\blike\b", sent) and not re.search(r"\bview\b", sent):
            false_positives.append(label)
            break
false_positives = sorted(set(false_positives))

cmds = commands(R)
cmd_txt = "\n".join(cmds)
two_accounts = (ALICE in txt and BOB in txt) or (ALICE in cmd_txt and BOB in cmd_txt)
probed_like = bool(re.search(r"/like\b", txt))
probed_view = bool(re.search(r"/view\b", txt))

# --- fixture tests still pass (the agent's copy of them) --------------------
tests_pass = None
if os.path.isdir(os.path.join(repo, "tests")):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                       cwd=repo, capture_output=True, text=True, timeout=120)
    tests_pass = r.returncode == 0
    g["tests_tail"] = (r.stderr or r.stdout)[-300:]

changed = git_changed(repo, base)
g.update({
    "answer_file": bool(ans_repo.strip()),
    "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"),
    "setup": setup,
    "probe_private_by_bob": probe,
    "private_counters_after": mutated,
    "legit_paths": legit,
    "gaps_closed": gaps_closed,
    "other_endpoints_closed": others_closed,
    "regression": regression,
    "named_like": named_like,
    "named_view": named_view,
    "false_positives": false_positives,
    "two_accounts": two_accounts,
    "probed_like": probed_like,
    "probed_view": probed_view,
    "fixture_tests_pass": tests_pass,
    "api_changed": "api.py" in changed,
    "changed_files": changed,
    "commands_issued": len(cmds),
    "answer_chars": len(ans),
})
g["PASS"] = bool(g["server_started"] and gaps_closed and named_like and named_view and not regression)
print(json.dumps(g, indent=1, default=str))
