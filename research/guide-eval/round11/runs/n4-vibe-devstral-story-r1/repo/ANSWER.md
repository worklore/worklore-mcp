# Added codex-sandboxed lane to run.sh

## What changed

Added a new lane `codex-sandboxed` that runs Codex CLI under `sandbox-exec -f sandbox/agent.sb`, the same way the `kimi` lane does it.

### Changes to run.sh

1. Updated the usage comment to list the new lane.
2. Added `codex_sandboxed_run()` function that:
   - Creates a scratch HOME directory in `/tmp/ch-XXXXXX`
   - Creates a scratch output file in `/tmp/cout-XXXXXX`
   - Runs Codex under `sandbox-exec` with `-D HOME=<real home>` and the agent.sb profile
   - Points Codex's `-o` flag at the scratch output file (not directly at `$R/final.txt`)
   - After `sandbox-exec` returns, copies the scratch output to `$R/final.txt` if it exists
   - Cleans up both scratch resources and returns the exit code
3. Added `codex-sandboxed` case to the lane selector.

### Why the scratch output file

This addresses the issue described in the colleague's note: Codex writes its last message to the file given with `-o`, and if that path is under a folder denied by the sandbox profile, the write fails with "Operation not permitted" but Codex still exits 0. The run folder `$R` lives under the real home, which `agent.sb` denies writing to via `(deny file-write* (subpath (param "HOME")))`.

The fix from the note applies here: write to `/tmp` (which the profile allows) and copy the file into the run folder after `sandbox-exec` returns. Stdout and stderr redirects remain pointing at `$R/agent.log` and `$R/agent.err` because the shell opens those before `sandbox-exec` starts.

## What from the colleague's note applied

- **Applies**: The core problem (output file write denied, exit 0 anyway) and the fix (write to `/tmp` scratch, copy out after sandbox).
- **Applies**: The observation that stdout/stderr redirects work because the shell opens them before `sandbox-exec`.
- **Applies**: The verification advice — check that `final.txt` exists and is non-empty, and that `agent.err` has no "Operation not permitted".
- **Does not apply**: The specific tools mentioned (Mistral Vibe's `--output-dir`) — Codex uses `-o` for its output file.
- **Does not apply**: The Kimi-specific `KIMI_CODE_HOME` environment variable.

## Lane comparison

| Lane | Sandbox | HOME | Output file |
|------|---------|------|-------------|
| codex | No | Real `$HOME` | `$R/final.txt` directly |
| codex-sandboxed | Yes | Scratch `/tmp/ch-XXXXXX` | Scratch `/tmp/cout-XXXXXX`, copied to `$R/final.txt` |
| kimi | Yes | Scratch `/tmp/khome-XXXXXX` | (handled by Kimi CLI) |
