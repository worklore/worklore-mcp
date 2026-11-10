# Changes Made

## Summary
Added a `codex-sandboxed` lane to `run.sh` that runs the Codex CLI inside the sandbox profile `sandbox/agent.sb`, mirroring how the `kimi` lane operates. This prevents the agent's shell from reading or writing to the real home directory.

## Files Modified

### 1. `run.sh`
- Updated the usage comment to document the new `codex-sandboxed` lane
- Added `codex_sandboxed_run()` function that:
  - Creates a temporary scratch HOME directory (`/tmp/chome-XXXXXX`)
  - Sets `CODEX_HOME` environment variable to point to `$REAL/.codex`
  - Runs Codex CLI under `sandbox-exec` with the `sandbox/agent.sb` profile
  - Uses the same Codex command flags as the unsandboxed `codex` lane
  - Cleans up the temporary directory after execution
- Added `codex-sandboxed` case to the lane selector

### 2. `sandbox/agent.sb`
- Added two new rules to allow read/write access to `~/.codex` directory:
  - `(allow file-read-data (subpath (string-append (param "HOME") "/.codex")))`
  - `(allow file-write* (subpath (string-append (param "HOME") "/.codex")))`
- These mirror the existing rules for `~/.kimi-code`

## Behavior
The `codex-sandboxed` lane now:
- Runs the same Codex CLI command as the `codex` lane
- Uses a scratch HOME directory for the agent's shell
- Can only access `~/.codex` in the real home directory (via sandbox rules)
- Cannot read or write any other files in the real home directory
- Produces the same output files in `runs/` as other lanes
