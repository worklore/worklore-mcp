## Changes Made

* **run.sh** – expanded the lane documentation to include a new `codex-sandboxed` lane.
* Implemented `codex_sandboxed_run()` which mirrors the behavior of the existing `kimi` lane:
  * Creates a temporary HOME directory.
  * Executes `codex exec` inside `sandbox/agent.sb` using `sandbox-exec` so the real `$HOME` is hidden from the agent.
  * Cleans up the temporary HOME after execution.
* Updated the case statement to dispatch `codex-sandboxed` to the new function.

The new lane provides the same Codex execution as the original `codex` lane but runs within the sandbox, preventing the agent from accessing the real home directory.

All modifications are confined to the repository root and respect the existing script structure.

