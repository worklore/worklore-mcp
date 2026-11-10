# Added codex-sandboxed lane to run.sh

## What I did

Added a new lane `codex-sandboxed` that runs the Codex CLI under `sandbox-exec -f sandbox/agent.sb`, the same way the `kimi` lane does it. This prevents the agent's shell from reading or writing the real home directory.

### Changes to run.sh

1. **Added `codex_sandboxed_run()` function** (lines 27-34):
   - Creates two scratch folders in `/tmp`: one for the sandboxed HOME (`/tmp/chome-XXXXXX`) and one for Codex's output file (`/tmp/cs-XXXXXX`)
   - Runs `codex exec` under `sandbox-exec` with `-D HOME="$REAL"` and the `agent.sb` profile
   - Points Codex's `-o` flag to `$SCRATCH/final.txt` (in `/tmp`, which the profile allows)
   - After `sandbox-exec` returns, copies `final.txt` from the scratch folder to the run folder `$R/final.txt`
   - Cleans up both scratch folders
   - Returns the exit code from the sandboxed command

2. **Updated the lane selector** (line 40): Added `codex-sandboxed) codex_sandboxed_run;;` case

3. **Updated usage comment** (lines 2-4): Added `codex-sandboxed` to the lane list with its description

## What applied from the colleague's note

The colleague's note **applied directly** to this case:

- **Problem identified**: Codex CLI writes its final message to the file given with `-o`, and that file was in the run folder under the real home directory. Inside the sandbox, that write is denied by the `deny file-write*` rule for `(subpath (param "HOME"))`.

- **Fix applied**: Point Codex's `-o` flag at a scratch folder in `/tmp` (which the profile allows), then copy the file into the run folder after `sandbox-exec` returns.

- **The note's check list**:
  - Output-file flag: `-o "$R/final.txt"` in the original `codex_run()` → falls under denied path
  - After fix: `-o "$SCRATCH/final.txt"` where `$SCRATCH` is `/tmp/cs-XXXXXX` → allowed
  - stdout/stderr redirects remain direct to the run folder (opened by the shell before `sandbox-exec` starts)

The note's reproduction steps and verification were followed: output path moved to `/tmp`, files copied after sandbox exits, and the exit code is not trusted alone (the grader checks for the final answer file).

## What did not apply

- The colleague mentioned Mistral Vibe's `--output-dir` flag having the same issue. This lane only uses Codex CLI, so that part was not relevant.
- The specific error messages and paths from their environment were examples, not instructions to copy.
