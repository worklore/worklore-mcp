# Summary of Changes

## 1. Added `codex-sandboxed` Lane in `run.sh`
- Added the `codex-sandboxed` option to the case statement and usage header in `run.sh`.
- Created the function `codex_sandboxed_run()` that mirrors `kimi_run()`'s sandboxing setup while executing the Codex CLI commands:
  - Creates a temporary scratch `$HOME` directory in `/tmp` (`SH=$(mktemp -d /tmp/chome-XXXXXX)`) so Codex cannot read or write the user's real home directory.
  - Passes `-D HOME="$REAL"` to `sandbox-exec` using the profile `sandbox/agent.sb` (`(deny file-read-data (subpath (param "HOME")))` and `(deny file-write* (subpath (param "HOME")))`).
  - Sets `export HOME="$SH"` within the subshell execution.
  - Cleans up scratch directories upon exit while capturing and returning the command's exit code.

## 2. Updated README.md
- Documented the new `codex-sandboxed` lane description in `README.md`.

## 3. Colleague Note Analysis: What Applied vs. What Was Ignored

### Parts that applied:
- **Writing to a temporary scratch folder outside the denied path (`/tmp`) for the `-o` output flag**:
  In `agent.sb`, file writes to the real home directory are denied (`(deny file-write* (subpath (param "HOME")))`). When runs take place inside a repository located under the user's home directory (as documented in `README.md`: `~/evals/agent-evals`), pointing `-o` directly to `$R/final.txt` will cause Codex inside `sandbox-exec` to fail writing `final.txt` with `Operation not permitted (os error 1)`.
  As noted in the colleague's memo, a scratch folder in `/tmp` (`SC=$(mktemp -d /tmp/cscratch-XXXXXX)`) was provided for `-o "$SC/final.txt"`. After `sandbox-exec` finishes, `final.txt` is copied from `$SC` into `$R/final.txt`, and `$SC` is removed.
- **Keeping stdout (`agent.log`) and stderr (`agent.err`) redirected directly into the run folder `$R`**:
  As noted, stdout and stderr redirects are opened by the parent shell before `sandbox-exec` starts, so they remain unaffected by sandbox path restrictions.

### Parts that did not apply / were ignored:
- **Mistral Vibe specifics (`--output-dir`, Mistral CLI flags)**: Not applicable since this harness only runs Codex and Kimi.
- **Inspection and debugging commands (`grep -l "Operation not permitted" runs/*/agent.err`)**: These were diagnostic recommendations from the note rather than implementation requirements.
