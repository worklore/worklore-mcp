# Answer

## What was added
* Added a **`codex-sandboxed`** lane to `run.sh`.
* Implemented `codex_sandboxed_run()` which mirrors the existing `kimi` lane:
  * Executes the Codex CLI inside the macOS sandbox defined by `sandbox/agent.sb`.
  * Uses a temporary fake `HOME` (via `mktemp -d /tmp/khome-XXXXXX`) so the agent cannot read/write the real home directory.
  * Writes Codex’s final message to a **scratch directory** (`/tmp/codex-sb-XXXXXX`) that is outside the sandboxed paths.
  * After the sandbox finishes, copies the `final.txt` from the scratch location back into the run folder.
  * Cleans up both the fake home and scratch directories.
* Updated the lane selector in `run.sh` to handle the new `codex-sandboxed` option.
* Updated the lane description comment at the top of `run.sh`.

## Parts of the colleague’s note that were applied
* **Sandbox profile usage** – The `sandbox-exec -f sandbox/agent.sb` pattern from the `kimi` lane was reused.
* **Preventing reads/writes to real `$HOME`** – Same `HOME` substitution (`-D HOME="$REAL"`) and fake home directory.
* **Scratch folder in `/tmp`** – Created a temporary directory (`SCR`) for Codex’s `-o` output, exactly as the colleague did to avoid the sandbox denial.
* **Copying out the result after sandbox execution** – After the sandbox run, the script copies `final.txt` from the scratch folder back into the run folder, matching the fix described.
* **Cleanup** – Both the fake home (`SH`) and scratch (`SCR`) directories are removed after the run.

The other details from the note (e.g., the specific error messages, handling of other agents like Mistral Vibe) were not needed for this task.

## Result
Running:

```bash
./run.sh <task> codex-sandboxed
```

executes Codex in a sandboxed environment where it cannot touch the real home directory, while still producing the expected `final.txt`, `agent.log`, and other artifacts inside the run folder.

