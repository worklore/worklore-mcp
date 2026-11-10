## Changes Made

* **`run.sh`**
  * Updated the lane description header to list the new `codex-sandboxed` lane.
  * Implemented `codex_sandboxed_run()` which runs Codex inside the same
    sandbox profile used by the `kimi` lane.
    * Creates a temporary empty `$HOME` (`SANDBOX_HOME`) and a scratch directory
      (`SCRATCH`) where Codex can safely write its `final.txt`.
    * Executes `codex exec` via `sandbox-exec -f sandbox/agent.sb` with `-D HOME`
      pointing to the real home (so the profile can deny access to it).
    * After the sandbox exits, copies `final.txt` from the scratch area back into
      the run folder (`$R/final.txt`) and cleans up temporary directories.
  * Added a case branch `codex-sandboxed)` to invoke the new function.
  * Updated the lane comment block to document the new lane.

## Applied Parts of the Colleague Note

* **Use a scratch folder outside denied paths** – the note suggested writing the
  agent’s output to a temporary directory in `/tmp`.  This implementation mirrors
  that by creating `$SCRATCH` with `mktemp -d /tmp/codex-scratch-XXXXXX`.
* **Copy the result back after the sandbox** – after the sandboxed process
  finishes, the script copies `final.txt` from the scratch folder into the run
  folder, exactly as described.
* **Keep stdout/stderr redirection outside the sandbox** – the redirection of
  `agent.log` and `agent.err` continues to happen in the outer shell, which opens
  the files before `sandbox-exec` starts, matching the note’s observation.

## How to Use the New Lane

```bash
./run.sh <task> codex-sandboxed [rep]
```

The command behaves like the original `codex` lane but runs the Codex CLI inside
the macOS sandbox profile (`sandbox/agent.sb`).  The agent cannot read or write
the real `$HOME`, and its output is safely captured in the run directory.

---

*The script still respects the existing `codex` (unsandboxed) and `kimi` lanes*
*so existing workflows remain unchanged.*

