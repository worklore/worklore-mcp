"""s3: silent launchd job. Hidden answer key (launchctl-print.txt: runs = 6, last exit code = 1; the
stderr log the plist points at holds both errors):
  Bug 1: `claude -p` under launchd fails with "Not logged in" — the CLI cannot reach its keychain login
         because USER is not set in the job's environment. Fix: set USER in the plist's
         EnvironmentVariables (or export it in the script; or provide an API key env var).
  Bug 2: the script assigns `status=$?` under zsh; `status` is a read-only zsh variable, so the
         script dies on line 19, BEFORE the failure notification. That is why nothing ever arrives.
         Fix: rename the variable (rc=$?), or run the script with bash.
PASS = both causes named in ANSWER.md, the status assignment is gone (or the shebang/program is no
       longer zsh), and a fix for the login problem is applied (USER set, or an API key env var).
Extra: ANSWER cites the runs count / exit code (checked reality first); notifier moved up / tested.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import read, run_text, git_changed, commands, answer

R = sys.argv[1]; repo = os.path.join(R, "repo"); base = read(os.path.join(R, "base_commit")).strip()
ans_repo = read(os.path.join(repo, "ANSWER.md")); ans = answer(R)
script = read(os.path.join(repo, "bin", "nightly-review.zsh"))
plist = read(os.path.join(repo, "Library", "LaunchAgents", "com.vk.nightly-review.plist"))
alt_scripts = ""
for root, _, files in os.walk(os.path.join(repo, "bin")):
    for f in files:
        alt_scripts += read(os.path.join(root, f))
txt = run_text(R)

status_assign = bool(re.search(r"^\s*status=", script, re.M)) or bool(re.search(r"\bstatus=\$\?", alt_scripts))
runs_with_zsh = ("/bin/zsh" in plist and "nightly-review.zsh" in plist) or script.startswith("#!/bin/zsh") or script.startswith("#!/usr/bin/env zsh")
bug2_fixed = (not status_assign) or (not runs_with_zsh)
user_set = bool(re.search(r"<key>USER</key>", plist)) or bool(re.search(r"^\s*export\s+USER=", script, re.M)) or bool(re.search(r"^\s*USER=", script, re.M))
api_key = bool(re.search(r"ANTHROPIC_API_KEY|CLAUDE_CODE_OAUTH_TOKEN", plist + script))
bug1_fixed = user_set or api_key
ans_l = ans.lower()
bug1_named = bool(re.search(r"not logged in|keychain|\busername\b|\buser\b.*(env|plist|variable)|login", ans_l))
bug2_named = bool(re.search(r"read-only|readonly|read only|\bstatus\b.{0,60}(zsh|reserved|built-?in|special)", ans_l))
notifier_downstream = bool(re.search(r"before (the )?(notif|messenger)|never reach|died before|dies before|exits before|killed? (the )?(script|messenger)|notif.{0,40}(never|not) (ran|run|reached|called|sent)", ans_l))
checked_reality = bool(re.search(r"runs\s*=\s*6|last exit code|exit code 1|ran 6|six times|6 times", ans_l))
cmds = commands(R)
launchctl_run = any(re.search(r"\blaunchctl\b", c) for c in cmds)
notify_run = any(re.search(r"notify\.sh|api\.telegram\.org", c) for c in cmds)

g = {
  "answer_file": bool(ans_repo.strip()), "answer_source": "repo" if ans_repo.strip() else ("brain" if ans.strip() else "none"), "status_assignment_left": status_assign, "runs_with_zsh": runs_with_zsh, "bug2_fixed": bug2_fixed,
  "USER_set": user_set, "api_key_env": api_key, "bug1_fixed": bug1_fixed,
  "bug1_named": bug1_named, "bug2_named": bug2_named, "explains_notifier_downstream": notifier_downstream,
  "cites_runs_or_exit_code": checked_reality, "launchctl_invoked": launchctl_run, "notifier_invoked": notify_run,
  "changed_files": git_changed(repo, base), "commands_issued": len(cmds), "answer_chars": len(ans),
}
g["PASS"] = bug1_named and bug2_named and bug2_fixed and bug1_fixed
print(json.dumps(g, indent=1))
