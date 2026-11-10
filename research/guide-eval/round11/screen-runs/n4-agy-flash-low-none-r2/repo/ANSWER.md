# Implementation Summary: codex-sandboxed Lane

Added the `codex-sandboxed` lane to `run.sh` to run the same Codex CLI execution as the `codex` lane within the macOS sandbox environment (`sandbox/agent.sb`), preventing the agent shell from reading or writing to the real user home directory.

## Key Changes Made

1. **Created `codex_sandboxed_run()` in [`run.sh`](file:///tmp/h-JtqllZ/run.sh)**:
   - Allocates an empty scratch directory for `HOME` via `mktemp -d /tmp/chome-XXXXXX`.
   - Executes Codex within a subshell with `export HOME="$SH"` under macOS sandbox using:
     ```bash
     sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
       timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json \
       -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"
     ```
   - Captures the return code and cleans up the scratch `HOME` directory.

2. **Updated Lane Routing in [`run.sh`](file:///tmp/h-JtqllZ/run.sh)**:
   - Added `codex-sandboxed) codex_sandboxed_run;;` to the `case $A in` dispatch block.
   - Updated the comment header documentation at the top of [`run.sh`](file:///tmp/h-JtqllZ/run.sh).
