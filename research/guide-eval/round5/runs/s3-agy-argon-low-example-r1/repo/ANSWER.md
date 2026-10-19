# Root Causes & Fixes for Silent `com.vk.nightly-review` Job

## 1. Root Causes Found

Inspection of `launchctl-print.txt` (`runs = 6`, `last exit code = 1`) and `Library/Logs/nightly-review.err` revealed **two stacked failures** (plus an additional launchd stdin trap for `claude -p`):

1. **`claude -p` failed due to missing `USER` environment variable (`Not logged in · Please run /login`)**:
   - In `Library/LaunchAgents/com.vk.nightly-review.plist`, `EnvironmentVariables` only defined `PATH`.
   - Under `launchd`, `USER` is not set by default in the environment (as seen in `launchctl-print.txt`). Without `USER=vk`, the `claude` CLI cannot look up its authentication credentials in the macOS Keychain and immediately exits with `Not logged in · Please run /login`.
2. **Failure notification was killed by assigning to read-only `status` in `zsh` (`read-only variable: status`)**:
   - In `bin/nightly-review.zsh` (line 19), the script captured the exit code of `claude` with `status=$?`.
   - In `zsh`, `status` is a read-only special built-in variable (an alias for `$?`). Attempting to assign to `status` caused `zsh` to abort the script immediately on line 19, before line 21 (`if [ $status -ne 0 ]`) could call `bin/notify.sh`. This made the failure completely silent.
3. **Unclosed stdin / multi-line prompt argument with `claude -p` under `launchd`**:
   - `bin/nightly-review.zsh` invoked `claude -p "$PROMPT" --output-format text > "$OUT"` without closing stdin (`< /dev/null`) or piping the prompt via stdin (`print -r -- "$PROMPT" | claude -p ...`), which under `launchd` can cause `claude -p` to hang waiting on stdin or fail multi-line prompt handling once authentication succeeds.

---

## 2. Which Parts of the Colleague's Note Applied (and Which Did Not)

### Applied:
- **Checking `launchctl print` and `StandardErrorPath` logs first**:
  - `launchctl-print.txt` confirmed the job *did* run 6 times (`runs = 6`) and failed every time (`last exit code = 1`), proving the issue was script execution/reporting rather than `launchd` scheduling.
  - `Library/Logs/nightly-review.err` contained the exact two error lines for all 6 runs.
- **Zsh `status=$?` read-only variable bug**:
  - Directly applied. Line 19 of `bin/nightly-review.zsh` had `status=$?`, producing `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status` in `nightly-review.err` and killing the script before `notify.sh` could run. Replaced with `rc=$?`.
- **Setting `USER` in the plist's `EnvironmentVariables`**:
  - Directly applied. The colleague's 2026-09-30 correction noted that without `USER` in `EnvironmentVariables`, `claude -p` cannot find its login in the keychain and dies with `"Not logged in"`. That exact error (`Not logged in · Please run /login`) was the primary failure in `nightly-review.err`. Added `<key>USER</key><string>vk</string>` to `Library/LaunchAgents/com.vk.nightly-review.plist`.
- **Piping the prompt via stdin (or closing stdin `< /dev/null`) for `claude -p`**:
  - Applied as a preventive fix in `bin/nightly-review.zsh` (`print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"`) so `claude -p` receives a clean EOF on stdin and doesn't hang or choke on multi-line prompt arguments once logged in.
- **Logging duration and verifying non-empty output (`[ ! -s "$OUT" ]`)**:
  - Applied in `bin/nightly-review.zsh` so a zero-exit run that produced no output is still caught and reported, and run duration (`${SECONDS}s`) is logged.

### Did Not Apply:
- **The colleague's first bug (`Input must be provided either through stdin or as a prompt argument`) as the primary failure in the log**:
  - In our logs, `claude` did not fail with `"Input must be provided..."` — it failed earlier with `"Not logged in · Please run /login"` because `USER` was missing from the plist environment.
- **Running live `launchctl kickstart` verification**:
  - Because this directory is an offline snapshot of the home directory and ground rules prohibit touching anything outside the current directory or calling external services, live `launchctl` reloading and Telegram requests are not executed here.
