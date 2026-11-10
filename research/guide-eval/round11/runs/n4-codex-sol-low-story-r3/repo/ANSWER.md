# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command as
the `codex` lane under `sandbox/agent.sb`, with an empty temporary `HOME` and
the real home passed only to the sandbox profile for denial. The profile now
takes a lane-specific `AGENT_INSTALL` path: Kimi still has access to
`~/.kimi-code`, while sandboxed Codex has no real-home exception.

Codex writes its `-o` final message into a temporary `/tmp` directory. After
the sandbox exits, the lane copies a non-empty `final.txt` into the run folder
and treats a missing or empty message as an error, even if Codex exits 0.
Stdout and stderr still go directly to the run folder.

The colleague's note applied to the `-o` output path, the shell-opened log
redirects, and the need to check the answer file as well as the exit code.
Its Mistral Vibe details and historical run results did not apply here.

Verified with `bash -n run.sh`, a sandbox profile load using `sandbox-exec`,
and `git diff --check`. I did not run a Codex smoke test because that would
send the task to an external service, which the ground rules prohibit.
