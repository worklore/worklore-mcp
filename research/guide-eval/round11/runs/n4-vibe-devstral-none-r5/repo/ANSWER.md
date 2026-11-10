# Changes Made

## Summary
Added a `codex-sandboxed` lane to `run.sh` that runs the Codex CLI inside the sandbox profile `sandbox/agent.sb`, mirroring how the `kimi` lane works. This prevents the agent's shell from reading or writing to the real home directory.

## Files Modified

### 1. `run.sh`
- Updated the usage comment to document the new `codex-sandboxed` lane
- Added `codex_sandboxed_run()` function that:
  - Creates a temporary scratch HOME directory (`/tmp/chome-XXXXXX`)
  - Runs Codex under `sandbox-exec` with the `sandbox/agent.sb` profile
  - Passes the real HOME as a parameter to the sandbox
  - Uses the same Codex command as the unsandboxed `codex` lane
  - Cleans up the temporary directory after execution
- Added `codex-sandboxed` case to the lane selector

### 2. `sandbox/agent.sb`
- Added rules to allow read/write access to `~/.codex` directory (Codex's config directory)
- This mirrors the existing rules for `~/.kimi-code`
- The sandbox still denies all other access to the real HOME directory

## Key Design Decisions

1. **Sandbox profile reuse**: The `codex-sandboxed` lane uses the same `sandbox/agent.sb` profile as the `kimi` lane, maintaining consistency.

2. **Temporary HOME**: Like the `kimi` lane, `codex-sandboxed` creates a temporary directory for HOME to isolate the agent's shell.

3. **Codex config access**: Added explicit allow rules for `~/.codex` so Codex can access its configuration files while still being sandboxed from the rest of the home directory.

4. **Command parity**: The `codex-sandboxed` lane uses the exact same Codex command as the unsandboxed `codex` lane, ensuring identical behavior except for the sandbox constraints.
