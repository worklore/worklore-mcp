# Changes Implemented

Added the `codex-sandboxed` lane to `run.sh`:
- Created `codex_sandboxed_run()` which runs `codex exec` under macOS `sandbox-exec` using `sandbox/agent.sb` with `-D HOME="$REAL"` and an isolated temporary scratch `HOME` directory (`mktemp -d /tmp/chome-XXXXXX`), matching the execution pattern used by the `kimi` lane.
- Cleaned up the temporary scratch directory after execution.
- Added `codex-sandboxed` to the lane selector `case` statement and updated the header usage comments.
