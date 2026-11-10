# Changes Made

## Summary
Added a `codex-sandboxed` lane to `run.sh` that runs the Codex CLI inside the sandbox profile (`sandbox/agent.sb`), mirroring how the `kimi` lane operates. This prevents the agent's shell from reading or writing to the real home directory.

## Files Modified

### 1. `run.sh`
- Updated the usage comment to document the new `codex-sandboxed` lane
- Added `codex_sandboxed_run()` function that:
  - Creates a temporary scratch HOME directory (`/tmp/chome-XXXXXX`)
  - Runs Codex CLI under `sandbox-exec` with the `sandbox/agent.sb` profile
  - Passes the real HOME via `-D HOME="$REAL"` parameter
  - Uses the same Codex command flags as the unsandboxed `codex` lane
  - Cleans up the temporary directory after execution
- Added `codex-sandboxed` case to the lane selector

### 2. `sandbox/agent.sb`
- Added two new allow rules to permit Codex access to its configuration directory:
  - `(allow file-read-data (subpath (string-append (param "HOME") "/.codex")))`
  - `(allow file-write* (subpath (string-append (param "HOME") "/.codex")))`
- These mirror the existing rules for `.kimi-code` and ensure Codex can read/write its own config while the rest of the home directory remains protected

## Design Decisions
- The sandboxed Codex uses the same command-line arguments as the unsandboxed version
- The temporary directory prefix is `chome-` (for Codex home) to distinguish from Kimi's `khome-`
- The sandbox profile was extended rather than duplicated to maintain a single source of truth for the security policy
