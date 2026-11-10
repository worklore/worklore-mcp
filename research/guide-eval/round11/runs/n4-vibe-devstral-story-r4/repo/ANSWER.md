# Added codex-sandboxed lane to run.sh

## What I did

Added a new lane `codex-sandboxed` to `run.sh` that runs Codex CLI under `sandbox-exec -f sandbox/agent.sb`, the same way the `kimi` lane does it. This prevents the agent's shell from reading or writing the real home directory.

### Changes to run.sh

1. Updated the usage comment to document the new lane.
2. Added `codex_sandboxed_run()` function that:
   - Creates a scratch HOME directory in `/tmp/chome-XXXXXX` (like kimi)
   - Creates a scratch output directory in `/tmp/cscratch-XXXXXX` for Codex's `-o` output
   - Runs Codex under `sandbox-exec` with the same sandbox profile (`sandbox/agent.sb`)
   - Copies `final.txt` from the scratch folder to the run folder after sandbox-exec returns
   - Cleans up both scratch directories
3. Added the new lane to the case statement.

## Colleague's note: what applied

The note "Codex lost its answer inside sandbox-exec and still exited 0" **applied directly**.

The problem it describes is exactly what would happen if we pointed Codex's `-o` flag at the run folder (which lives under the user's home directory): the sandbox profile denies file writes to the home directory, so Codex would fail to write `final.txt` with "Operation not permitted" and still exit 0. The grader would then see an empty final answer.

The fix from the note is what I implemented: write Codex's output to a scratch folder in `/tmp` (which the profile allows), then copy it to the run folder after `sandbox-exec` returns. The stdout/stderr redirects remain pointing to the run folder because the shell opens them before `sandbox-exec` starts.

### Specific parts used:
- The diagnosis: output-file flags (`-o`) pointing to denied paths fail silently (exit 0) with "Operation not permitted"
- The fix pattern: scratch folder in `/tmp`, copy files out after sandbox exits
- The verification guidance: check that result file exists and stderr has no "Operation not permitted"

### Parts not used:
- The Kimi-specific details (KIMI_CODE_HOME, Moonshot) don't apply to Codex
- The Mistral Vibe CLI specifics don't apply here
