# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command and
produces the same run artifacts as `codex`, while launching it through
`sandbox-exec` with `sandbox/agent.sb`. It uses temporary `HOME` and `CODEX_HOME`
directories, which are removed after the run.

The profile now takes a lane-specific `AGENT_INSTALL` path. Kimi keeps access
to `~/.kimi-code`; the Codex lane opens only its scratch workspace, so the
profile's real-home read and write denials apply to Codex. Updated the lane
list in `README.md`.

Verified `run.sh` with `bash -n`, checked the diff for whitespace errors, and
confirmed the profile starts successfully and denies reading a file in the
real home. I did not launch a full agent run.
