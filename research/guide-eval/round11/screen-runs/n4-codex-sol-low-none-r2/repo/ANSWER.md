# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command and writes the same output files as `codex`, but launches through `sandbox-exec` with a temporary HOME. The temporary HOME is removed after the run.

Updated `sandbox/agent.sb` to take a lane-specific `AGENT_INSTALL` exception. Kimi still has access to `~/.kimi-code`; the Codex lane's exception points only to its temporary HOME, so its shell cannot read or write the real home.

Verified `run.sh` with `bash -n` and checked that a shell under the Codex sandbox cannot read a file in, or write to, the real home. No Codex task was run, so live agent execution remains unverified.
