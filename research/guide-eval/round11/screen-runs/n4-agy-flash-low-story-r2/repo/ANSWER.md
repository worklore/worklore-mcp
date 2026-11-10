# Implementation Details: codex-sandboxed Lane

## Summary of Changes
Added a `codex-sandboxed` lane to [`run.sh`](file:///tmp/h-hgCCdA/run.sh) that runs the Codex CLI inside `sandbox/agent.sb` similar to the `kimi` lane:
- Sets up an isolated scratch `HOME` directory (`mktemp -d /tmp/chome-XXXXXX`) so the agent's shell cannot read or write to the user's real home folder.
- Executes under `sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb"`.
- Runs Codex with the same flags as the unsandboxed `codex` lane:
  `timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o "$SCRATCH/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err"`
- Cleans up temporary scratch directories upon completion and propagates the process return code.

## Colleague's Note: What Applied and What Was Ignored

### What Applied:
- **Scratch folder for output files**: The colleague noted that running under `sandbox-exec` with a profile denying writes to `$HOME` prevents the tool from writing output files (`-o`) directly into the run folder `$R`, because the run directory lives inside the repository (under the home folder). Writing `-o "$R/final.txt"` from inside the sandbox fails with `Operation not permitted` (even if Codex exits 0).
- **Writing to `/tmp` and copying after exit**: As recommended in the note, a scratch directory was created in `/tmp` (`SCRATCH=$(mktemp -d /tmp/cscratch-XXXXXX)`), Codex was directed to write `-o "$SCRATCH/final.txt"`, and the resulting file is copied to `$R/final.txt` after `sandbox-exec` finishes.
- **Redirection outside sandbox**: Standard output (`> "$R/agent.log"`) and standard error (`2> "$R/agent.err"`) were kept redirected directly to the run folder since the subshell opens those file descriptors before `sandbox-exec` executes.

### What Was Ignored:
- **Mistral Vibe specifics**: Notes regarding Mistral Vibe and `--output-dir` were not relevant as this lane only targets Codex.
- **Grader / eval-harness diagnostics**: Debugging steps such as grepping historical run folders (`runs/*/agent.err`) and inspecting past failures were not needed since we implemented the scratch output staging pattern directly up front.
