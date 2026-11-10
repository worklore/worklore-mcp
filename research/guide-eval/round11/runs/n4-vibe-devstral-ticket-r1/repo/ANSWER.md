Added a `codex-sandboxed` lane to `run.sh` that runs Codex inside `sandbox/agent.sb`, mirroring how the `kimi` lane works.

Changes to `run.sh`:
- Added `codex-sandboxed` to the lane list in the header comment
- Added `codex_sandboxed_run()` function that:
  - Creates a scratch HOME directory (`/tmp/chome-XXXXXX`) to pass as HOME inside the sandbox
  - Creates a scratch output directory (`/tmp/cscratch-XXXXXX`) for Codex's `-o` output file
  - Runs Codex under `sandbox-exec -f sandbox/agent.sb` with `-D HOME=$REAL`
  - After the sandboxed command returns, copies `final.txt` from the scratch folder to the run folder
  - Cleans up both scratch directories
- Added `codex-sandboxed` case to the lane selector

Colleague's note - what applied:
- The observation that Codex's `-o` flag writes inside the sandbox and is denied by the sandbox profile's `deny file-write*` rules applied directly. The run folder is under the real home, so writes to `$R/final.txt` would fail with "Operation not permitted".
- The fix of using a scratch folder in `/tmp` (outside all denied paths) for the output file, then copying it into the run folder after `sandbox-exec` returns, applied directly.
- The note that stdout/stderr redirects work because the shell opens them before `sandbox-exec` starts was already handled correctly - those redirects remain pointing to the run folder.

What did not apply:
- The specific flags `--output-last-message`, `--output-dir`, `--out` mentioned for other tools don't apply to Codex, which uses `-o`.
- The Mistral Vibe-specific details don't apply here.
- The grading/answer extraction logic was already in place via `check_answer.py` and `answer.json`.
