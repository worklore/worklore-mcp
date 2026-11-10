# Changes Made

## Added codex-sandboxed lane to run.sh

Added a new lane `codex-sandboxed` that runs Codex inside the macOS sandbox profile `sandbox/agent.sb`, the same way the `kimi` lane does it. This prevents the agent's shell from reading or writing to the real home directory.

### Key implementation details:

1. **Scratch HOME directory**: Like the kimi lane, the codex-sandboxed lane creates a temporary scratch HOME directory (`/tmp/chome-XXXXXX`) and sets `HOME` to it before invoking `sandbox-exec`. The real HOME is passed via `-D HOME="$REAL"` so the sandbox profile can reference it in its rules.

2. **Scratch output directory**: Following the colleague's note, Codex's `-o` flag (which writes the final message) would fail inside the sandbox because the run folder `$R` is under the real home. To solve this, I created a separate scratch folder in `/tmp` (`/tmp/cscratch-XXXXXX`) and pointed Codex's `-o` flag at `$SCRATCH/final.txt`. After `sandbox-exec` returns, the lane copies `final.txt` from the scratch folder to the run folder, then cleans up both scratch directories.

3. **Sandbox profile update**: Added rules to `sandbox/agent.sb` to allow read/write access to `~/.codex` (Codex's config/cache directory), mirroring the existing rules for `~/.kimi-code`.

4. **stdout/stderr handling**: Like the kimi lane, stdout and stderr are redirected directly to files in the run folder (`$R/agent.log` and `$R/agent.err`). This works because the shell opens these files before `sandbox-exec` starts, so the sandbox's deny rules don't apply to them.

## Parts of the colleague's note that applied:

- The observation that Codex's `-o` flag write fails inside the sandbox with "Operation not permitted" even though the process exits 0.
- The solution of using a scratch folder in `/tmp` (outside all denied paths) for the output file, then copying it to the run folder after the sandbox exits.
- The confirmation that stdout/stderr redirects work fine because the shell opens those files before `sandbox-exec` starts.

## Parts that did not apply:

- The specific mention of Mistral Vibe's `--output-dir` flag (we're only dealing with Codex here).
- The grading/validation details (our task was just to add the lane).
