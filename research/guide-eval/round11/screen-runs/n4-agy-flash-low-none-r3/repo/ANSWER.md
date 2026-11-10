# Changes Made

Added the `codex-sandboxed` lane to [`run.sh`](file:///tmp/h-fL7nHG/run.sh):

1. **Function `codex_sandboxed_run`**:
   - Replicated the sandboxing mechanism from `kimi_run`, capturing the real home (`REAL="$HOME"`) and provisioning a temporary scratch home (`SH=$(mktemp -d /tmp/chome-XXXXXX)`).
   - Executed Codex inside a subshell using `sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb"` with `HOME="$SH"`.
   - Executed the exact same Codex invocation as `codex_run` (`timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"`).
   - Cleaned up the scratch directory (`rm -rf "$SH"`) and returned the exit code.

2. **CLI Dispatch and Documentation**:
   - Updated the `case $A in` block in [`run.sh`](file:///tmp/h-fL7nHG/run.sh) to handle `codex-sandboxed) codex_sandboxed_run;;`.
   - Documented the lane in the usage comments header in [`run.sh`](file:///tmp/h-fL7nHG/run.sh).
