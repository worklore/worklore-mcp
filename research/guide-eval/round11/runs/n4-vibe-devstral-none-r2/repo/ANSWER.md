# Changes Made

## Summary
Added a `codex-sandboxed` lane to `run.sh` that runs Codex CLI inside the sandbox profile `sandbox/agent.sb`, mirroring how the `kimi` lane operates. This prevents the agent's shell from reading or writing to the real home directory.

## Files Modified

### 1. `run.sh`
- Updated the usage comment to document the new `codex-sandboxed` lane
- Added `codex_sandboxed_run()` function that:
  - Creates a temporary scratch HOME directory (`/tmp/chome-XXXXXX`)
  - Uses `sandbox-exec` with `-D HOME="$REAL"` to pass the real home directory
  - Uses `-f "$D/sandbox/agent.sb"` to apply the sandbox profile
  - Sets `HOME` to the scratch directory for the agent's shell
  - Runs the same Codex command as the unsandboxed `codex` lane
  - Cleans up the scratch directory after execution
- Added `codex-sandboxed` case to the lane selector

### 2. `sandbox/agent.sb`
- Added rules to allow read access to Codex's installation directories:
  - `/opt/homebrew/lib/node_modules/@openai/codex` (Codex npm package)
  - `/opt/homebrew/bin/codex` (Codex CLI entry point)
- Added rules to allow read/write access to Codex's data directory in the real home:
  - `$(param "HOME")/.codex` (Codex config and cache)

## Behavior
The `codex-sandboxed` lane now:
1. Runs Codex CLI with the same command-line arguments as the unsandboxed `codex` lane
2. Executes within the sandbox profile that blocks access to the real home directory
3. Uses a temporary scratch HOME to prevent the agent from reading/writing real user files
4. Allows access only to Codex's installation and its own data directory under the real home
5. Maintains the same timeout (1200 seconds) and output structure as other lanes

## Usage
```bash
./run.sh <task> codex-sandboxed [rep]
```
