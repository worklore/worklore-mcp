# Added codex-sandboxed lane to run.sh

## What I did

1. **Updated `sandbox/agent.sb`**: Added two rules to allow file read/write access to `~/.codex` directory, mirroring the existing rules for `~/.kimi-code`. This lets the sandboxed Codex CLI access its configuration and cache in the real home while still denying access to the rest of the home folder.

2. **Added `codex_sandboxed_run()` function in `run.sh`**:
   - Creates two scratch directories: one for `HOME` (`/tmp/chome-XXXXXX`) and one for output files (`/tmp/cscratch-XXXXXX`)
   - Runs `codex exec` under `sandbox-exec -f sandbox/agent.sb` with:
     - `HOME` set to the scratch directory
     - Real home passed via `-D HOME="$REAL"`
     - `CODEX_HOME` set to `$REAL/.codex` so Codex can access its config
     - Output file (`-o`) directed to `$SCRATCH/final.txt` in the /tmp scratch folder
   - After `sandbox-exec` returns, copies `final.txt` from the scratch folder to the run folder
   - Cleans up both scratch directories

3. **Added lane to the case statement**: Added `codex-sandboxed` as a selectable lane.

4. **Updated usage comment**: Documented the new lane.

## Colleague's note: what applied

The note described exactly the problem this implementation avoids: Codex writes its last message to the `-o` file, and inside a sandbox that denies writes to the run folder (which is under the real home), that write fails with "Operation not permitted" but Codex still exits 0.

**Parts that applied:**
- The problem: output file paths under denied folders cause silent failures
- The fix: write output to a /tmp scratch folder and copy it out after sandbox-exec returns
- The verification: check that result files exist and stderr has no "Operation not permitted"

**Parts that did not apply:**
- The note's specific mention of Mistral Vibe's `--output-dir` flag (we're using Codex's `-o` flag)
- The note's mention of macOS-specific behavior beyond sandbox-exec itself

## Key design decisions

- Used the same sandbox profile (`sandbox/agent.sb`) as the kimi lane, extended with `.codex` access rules
- Followed the kimi lane pattern: scratch HOME, `-D HOME` parameter, environment variable for the tool's home directory
- Output file goes to /tmp scratch, copied back after sandbox-exec (addressing the colleague's note)
- stdout/stderr redirects remain direct to the run folder (the shell opens them before sandbox-exec starts)
