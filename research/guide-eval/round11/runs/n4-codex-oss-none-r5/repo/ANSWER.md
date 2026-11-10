Implemented a **`codex-sandboxed` lane** in `run.sh`:

- Updated the lane description header to list the new lane.
- Added a `codex_sandboxed_run` function that:
  1. Creates a temporary scratch `HOME`.
  2. Executes `codex exec` inside `sandbox/agent.sb` via `sandbox-exec` (mirroring the existing `kimi` lane).
  3. Writes output to the same locations as the regular `codex` lane.
  4. Cleans up the temporary `HOME` directory.
- Extended the `case` block to handle `codex-sandboxed` and invoke the new function.

**Usage**
```
./run.sh <task> codex-sandboxed [rep]
```
The lane behaves like the original `codex` lane but runs with the agent’s shell sandboxed, preventing reads/writes to the real `$HOME`.

No other files were altered.
