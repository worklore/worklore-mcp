# Changes Made

## Summary
Added a `codex-sandboxed` lane to `run.sh` that runs the Codex CLI inside the same sandbox profile (`sandbox/agent.sb`) used by the `kimi` lane, preventing the agent's shell from reading or writing the real home directory.

## Files Modified

### 1. `run.sh`
- Added `codex-sandboxed` to the usage comment in the header
- Added new function `codex_sandboxed_run()` that:
  - Creates a temporary scratch HOME directory (`/tmp/chome-XXXXXX`)
  - Uses `sandbox-exec` with the `-f "$D/sandbox/agent.sb"` profile
  - Passes the real HOME via `-D HOME="$REAL"` parameter
  - Runs the same Codex command as the unsandboxed `codex` lane: `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o "$R/final.txt" "$P"`
  - Cleans up the temporary directory after execution
- Added `codex-sandboxed` case to the lane switch statement

### 2. `sandbox/agent.sb`
- Added two new rules to allow the sandboxed process to access Codex's configuration directory:
  - `(allow file-read-data (subpath (string-append (param "HOME") "/.codex")))`
  - `(allow file-write* (subpath (string-append (param "HOME") "/.codex")))`
- These mirror the existing rules for `.kimi-code` and ensure Codex can read/write its own config while still being blocked from the rest of the real home directory

## Behavior
The `codex-sandboxed` lane now runs Codex with the same command-line arguments as the `codex` lane, but confined by the sandbox profile so the agent cannot access the real user home directory (except for its own `.codex` config folder).
