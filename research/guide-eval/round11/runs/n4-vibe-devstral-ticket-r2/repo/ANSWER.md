# Changes Made

## Summary
Added a `codex-sandboxed` lane to `run.sh` that runs Codex CLI under the macOS sandbox profile `sandbox/agent.sb`, preventing the agent's shell from reading or writing to the real home directory, similar to how the `kimi` lane operates.

## Files Modified

### 1. `run.sh`
- Added new lane `codex-sandboxed` to the usage comment
- Added `codex_sandboxed_run()` function that:
  - Creates a scratch HOME directory (`/tmp/chome-XXXXXX`) for the sandboxed process
  - Creates a scratch output directory (`/tmp/cscratch-XXXXXX`) to avoid sandbox write denials
  - Runs Codex CLI under `sandbox-exec` with the same flags as the unsandboxed `codex` lane
  - Points the `-o` output flag to the scratch directory to avoid the sandbox denial issue described in the colleague's note
  - Copies the final output from scratch to the run folder after sandbox-exec returns
  - Cleans up both scratch directories
- Added `codex-sandboxed` case to the lane switch

### 2. `sandbox/agent.sb`
- Added allow rules for `~/.codex` directory (read and write) to match the existing `~/.kimi-code` allowances
- This allows Codex to access its own configuration and cache while still denying access to the rest of the home directory

## Colleague's Note - What Applied

The following parts of the colleague's note were directly relevant and addressed:

1. **Sandbox write denials for output files**: The colleague found that Codex's `-o` flag write was denied by the sandbox, causing empty final answers despite exit code 0. This was fixed by using a scratch folder in `/tmp` for the output file.

2. **stdout/stderr redirects work**: The colleague noted that stdout and stderr redirects into the run folder worked because the shell opened those files before `sandbox-exec` started. We maintained this pattern - stdout/stderr go directly to the run folder, while the `-o` output goes to a scratch directory.

3. **Copy files after sandbox-exec returns**: The colleague's solution of copying files from the scratch folder to the run folder after `sandbox-exec` returns was implemented.

4. **Clean up scratch folders**: The colleague deleted scratch folders after use, which we also do.

The following parts did not apply:
- The specific mention of Mistral Vibe's `--output-dir` flag (we're only dealing with Codex here)
- The specific paths like `/tmp/...` patterns were examples; we used our own naming convention (`chome-XXXXXX` and `cscratch-XXXXXX`)
