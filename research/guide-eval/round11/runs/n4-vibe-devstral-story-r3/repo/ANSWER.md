# Added codex-sandboxed lane to run.sh

## What I did

Added a new lane `codex-sandboxed` that runs Codex CLI under `sandbox/agent.sb`, the same way the `kimi` lane does it, so the agent's shell cannot read or write the real home directory.

### Changes to run.sh

1. **Added `codex_sandboxed_run()` function** (lines 21-28):
   - Creates two scratch directories in `/tmp`: one for `HOME` (`/tmp/chome-XXXXXX`) and one for Codex's output file (`/tmp/co-XXXXXX`)
   - Sets `HOME` to the scratch directory and runs under `sandbox-exec -f sandbox/agent.sb` with `-D HOME="$REAL"` to pass the real home as a sandbox parameter
   - Points Codex's `-o` flag to `$SCRATCH_OUT/final.txt` instead of directly to `$R/final.txt`
   - After `sandbox-exec` returns, copies the output file from the scratch folder to the run folder if it exists
   - Cleans up both scratch directories
   - Returns the exit code from the sandboxed command

2. **Updated the lane selector** (lines 43-46):
   - Added `codex-sandboxed) codex_sandboxed_run;;` to the case statement

3. **Updated the usage comment** (lines 2-4):
   - Added documentation for the new `codex-sandboxed` lane

## Colleague's note: what applied

The colleague's note describes exactly the problem this change solves:
- Codex writes its final answer to the file given with `-o`
- Inside the sandbox, writes to the run folder (which is in the real home) are denied by the profile's `(deny file-write* (subpath (param "HOME")))` rule
- Codex prints `Failed to write last message file: Operation not permitted` to stderr but still exits 0
- The fix is to write to a scratch folder in `/tmp` (which the profile allows) and copy the file back after the sandbox exits

**Parts that applied:**
- The problem: output file writes denied inside sandbox, exit code 0 despite failure
- The solution: use a scratch folder in `/tmp` for output, copy back after sandbox-exec
- The verification: check that the result file exists in the run folder

**Parts that did not apply:**
- The note mentions Mistral Vibe's `--output-dir` flag, which we don't use here
- The note's reproduction steps and verification are general guidance, not specific instructions we needed to follow
