# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It uses the same Codex command and flags as
`codex`, but runs it through `sandbox-exec` with `sandbox/agent.sb`. The lane
passes the real home path to the profile's `HOME` parameter, while giving
Codex a temporary `HOME` and `CODEX_HOME` under `/tmp`. The shared profile's
Kimi exception is now parameterized: Kimi still opens its real `~/.kimi-code`,
while Codex points that exception at its scratch home. The Codex agent's shell
therefore cannot read or write the real home.

The Codex `-o` path is also under `/tmp`. After the sandboxed process exits,
the lane copies its `final.txt` into the run folder so `check_answer.py` can
read it. Stdout and stderr still go directly to `agent.log` and `agent.err`.
The lane preserves Codex's exit code and removes its temporary folders.
`README.md` now lists the lane.

## Colleague note

The relevant points were the denied run-folder write for Codex's `-o` file,
the use of an allowed scratch output path with a copy after `sandbox-exec`,
and the fact that outer-shell stdout and stderr redirects can still target
the run folder. The Kimi/Mistral Vibe `--output-dir` issue does not apply to
this Codex lane. The note's observed exit-0 failure is a reason to check
`final.txt`; it was not reproduced here.

## Verification

`bash -n run.sh` and `git diff --check` passed. A live Codex run was not made
because it would send task content to an external service, which the task's
ground rules prohibit.
