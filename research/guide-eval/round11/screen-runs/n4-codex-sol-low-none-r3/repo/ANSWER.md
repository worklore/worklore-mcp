# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command and writes the same run artifacts as `codex`, but launches it through `sandbox-exec` with `sandbox/agent.sb` and a temporary HOME/CODEX_HOME. The lane copies `auth.json` and `config.toml`, when present, into the temporary Codex directory before launch and deletes that directory afterward.

Updated `sandbox/agent.sb` to take an `AGENT_INSTALL` path. The Kimi lane passes its existing install path; the Codex lane passes its temporary Codex directory. The profile continues to deny access to the real home outside that lane-specific exception.

Verified with `bash -n run.sh`, a sandbox profile launch, and `git diff --check`. I did not run an agent task.
