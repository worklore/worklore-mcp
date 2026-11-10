# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same Codex command and writes the same run artifacts as `codex`, but launches Codex through `sandbox/agent.sb` with scratch `HOME` and `CODEX_HOME` directories. The scratch home is removed after the run.

Updated `sandbox/agent.sb` so its home-directory exception is selected per lane: Kimi retains access to its own install, while the Codex lane's exception points only to its scratch home. This prevents Codex's shell from reading or writing the real home.

Verified shell syntax with `bash -n run.sh`, compiled and launched the sandbox profile with `/usr/bin/true`, and checked the diff with `git diff --check`. I did not run a Codex task because that would contact an external service.
