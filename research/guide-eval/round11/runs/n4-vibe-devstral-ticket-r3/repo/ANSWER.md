# Changes Made

## Added codex-sandboxed lane to run.sh

Added a new lane `codex-sandboxed` that runs the Codex CLI under the macOS sandbox profile `sandbox/agent.sb`, mirroring how the `kimi` lane operates. This prevents the agent's shell from reading or writing to the real home directory.

### Key implementation details:

1. **Sandbox execution**: The Codex process runs under `sandbox-exec -f "$D/sandbox/agent.sb"` with `-D HOME="$REAL"` to pass the real home directory as a parameter to the sandbox profile.

2. **Scratch HOME**: A temporary directory is created in `/tmp/khome-XXXXXX` and set as `HOME` for the sandboxed process, preventing access to the real home.

3. **Output file handling**: Following the colleague's note, the Codex `-o` output file is written to a scratch folder in `/tmp/cscratch-XXXXXX` (outside the denied home path). After `sandbox-exec` returns, the file is copied to the run folder at `$R/final.txt` and the scratch folder is cleaned up.

4. **stdout/stderr**: These remain redirected directly to the run folder (`$R/agent.log` and `$R/agent.err`) because the shell opens these files before `sandbox-exec` starts, as noted by the colleague.

## Updated sandbox/agent.sb

Added allowances for Codex's typical configuration directory:
- `(allow file-read-data (subpath (string-append (param "HOME") "/.codex")))`
- `(allow file-write* (subpath (string-append (param "HOME") "/.codex")))`

This mirrors the existing allowances for Kimi Code's `~/.kimi-code` directory.

## Colleague's note - what applied

The following parts of the colleague's note were directly applicable:

1. **Sandbox denial of writes to run folder**: The run folder is inside the real home directory, which is denied by the sandbox profile's `deny file-write*` rules. This would cause Codex to fail when writing the `-o` output file.

2. **Solution using /tmp scratch folder**: Using `mktemp -d /tmp/...` for the output file path, then copying it back after the sandbox exits.

3. **stdout/stderr redirects work**: These are opened by the shell before `sandbox-exec` starts, so they're not subject to the sandbox restrictions.

4. **Exit code 0 doesn't guarantee success**: The colleague noted that both Codex and Mistral Vibe exited with code 0 even when file writes failed. This is why we must use the /tmp scratch approach.

The parts that did not apply:
- The specific mention of Mistral Vibe's `--output-dir` flag (we're only dealing with Codex here)
- The specific paths mentioned for the colleague's eval repository setup
