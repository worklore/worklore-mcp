Added the `codex-sandboxed` lane to `run.sh`. It runs the same Codex command as `codex` inside `sandbox/agent.sb` with scratch `HOME` and `CODEX_HOME` directories, then removes the scratch home.

The sandbox profile now takes a lane-specific `AGENT_HOME` exception: Kimi retains access to `~/.kimi-code`, while the Codex lane only opens its scratch home. Updated `README.md` with the new lane.

Verified `run.sh` syntax with `bash -n`, checked the diff with `git diff --check`, and confirmed the sandbox blocks reading an existing file in the real home. I did not launch a Codex run because that would contact an external service.
