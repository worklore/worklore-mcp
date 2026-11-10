# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command as
`codex` inside `sandbox/agent.sb`, with scratch `HOME` and `CODEX_HOME`.
The profile denies access to the real home. Its install exception is now
lane specific: Kimi retains access to `~/.kimi-code`; Codex gets only its
scratch directory.

The colleague's note applies to Codex's `-o` output: a run folder under the
real home would deny that write inside the sandbox, even if Codex exited 0.
The new lane writes `final.txt` to `/tmp`, then copies it into the run folder
after `sandbox-exec` exits. It keeps stdout and stderr redirected by the outer
shell and treats a missing final file after exit 0 as a failure. The note's
Mistral Vibe details do not apply to this harness.

Checked `bash -n run.sh`, `git diff --check`, and a `sandbox-exec` read probe
that confirmed the real home is denied. No live Codex run was made because it
would contact an external model provider.
