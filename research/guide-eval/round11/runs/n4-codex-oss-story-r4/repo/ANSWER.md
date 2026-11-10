Added a new **codex-sandboxed** lane to `run.sh`.

### What was changed
* Updated the lane description header to list the new lane.
* Implemented `codex_sandboxed_run()` which:
  - Creates a temporary HOME directory (`/tmp/codex-home-XXXXXX`).
  - Creates a scratch directory (`/tmp/codex-scratch-XXXXXX`) for the output file.
  - Runs `codex exec` inside `sandbox/agent.sb` with the temporary HOME.
  - Writes the final answer to the scratch folder (allowed by the sandbox).
  - Copies the resulting `final.txt` back into the run folder after the sandbox exits.
  - Cleans up temporary directories.
* Added the lane to the case statement (`codex-sandboxed) codex_sandboxed_run;;`).

### Parts of the colleague’s note that were applied
* **Use a scratch folder outside denied paths** – we create `/tmp/codex-scratch-XXXXXX` for the output, mirroring the note’s suggestion to write to a permitted location.
* **Copy the result out after sandbox‑exec finishes** – after the sandbox run we copy `final.txt` into `$R/final.txt`.
* **Temporary HOME inside sandbox** – follows the same pattern as the existing `kimi` lane, ensuring the agent cannot read/write the real home.

The rest of the note (e.g., checking stderr for “Operation not permitted”) was not needed for the implementation.

Now `run.sh <task> codex-sandboxed` behaves like the existing `codex` lane but with the sandbox restrictions applied.

