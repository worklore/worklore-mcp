# Implementation Summary: `codex-sandboxed` Lane

## 1. What was done

Added the `codex-sandboxed` lane to [`run.sh`](file:///tmp/h-C8tWoT/run.sh):
- Configured the lane to execute `codex` under `sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb"` matching the isolation pattern used by `kimi_run`.
- Provided an isolated scratch home folder (`SH=$(mktemp -d /tmp/chome-XXXXXX)`) exported as `HOME="$SH"` so the agent shell and tools cannot read or modify the user's real home folder.
- Seeded `$SH/.codex/auth.json` from `$REAL/.codex/auth.json` (if present) so Codex authenticates without accessing the real home directory.
- Created a separate scratch folder in `/tmp` (`SCRATCH=$(mktemp -d /tmp/cscratch-XXXXXX)`) and directed the `-o` output to `$SCRATCH/final.txt`.
- After `sandbox-exec` completes, copied `$SCRATCH/final.txt` to the run directory (`$R/final.txt`) and cleaned up both temporary directories (`$SH` and `$SCRATCH`).
- Preserved stdout and stderr redirections (`> "$R/agent.log" 2> "$R/agent.err"`), which are opened by the outer shell before `sandbox-exec` starts.
- Added `codex-sandboxed` to the lane selector and usage header comment in `run.sh`.

## 2. Colleagues' note: which parts applied and which did not

### Parts that applied:
- **Writing output to a scratch folder outside denied paths**: When the harness is located within or under the real user home directory (or in cases where run paths conflict with sandbox restrictions), pointing `-o` directly at the run folder would cause Codex to fail with `Operation not permitted` while exiting 0. Pointing `-o` to a temporary directory in `/tmp` (`$SCRATCH/final.txt`) and copying it to `$R/final.txt` after `sandbox-exec` finishes ensures `final.txt` is reliably captured.
- **Keeping stdout and stderr redirections straight into the run folder**: Redirections are managed by the host subshell prior to executing `sandbox-exec`, so standard file descriptors work as expected.
- **Cleaning up temporary scratch directories**: Deleting `$SH` and `$SCRATCH` upon completion of the lane execution.
- **Verification steps**: Validating that `final.txt` is populated, `answer.json` contains the expected output, and `agent.err` does not report "Operation not permitted".

### Parts that did not apply:
- **Mistral Vibe (`--output-dir`)**: Not used in this codebase (only Codex and Kimi are configured).
- **Inspecting existing failure logs (`grep -l "Operation not permitted" runs/*/agent.err`)**: `codex-sandboxed` is a new lane being added, not an existing broken lane with historic logs in the repository.
