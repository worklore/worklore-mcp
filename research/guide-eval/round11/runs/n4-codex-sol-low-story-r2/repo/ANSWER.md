# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It uses the same `codex exec` arguments as
`codex`, but runs under `sandbox/agent.sb` with a scratch `HOME`. The profile now
accepts a lane-specific `INSTALL` path: Kimi retains its `~/.kimi-code` access,
while Codex gets no real-home exception. Updated `README.md` with the new lane.

The colleague's note about `-o` applied: the sandbox cannot write `final.txt`
in a run folder under the real home. Codex now writes its last message to the
scratch folder in `/tmp`; the script copies it to the run folder after the
sandbox exits. Stdout and stderr still redirect to the run folder outside the
sandbox. A zero exit with no non-empty final message is treated as a failure.
The note's Mistral Vibe details did not apply because this harness has no Vibe
lane.

Verified with `bash -n run.sh`, `git diff --check`, and a local
`sandbox-exec` profile probe. I did not run a Codex smoke test because that
would contact an external service, which the task rules prohibit.
