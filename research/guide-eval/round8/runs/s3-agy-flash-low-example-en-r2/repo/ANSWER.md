# Causes of Silent Failure and Fixes

## 1. Causes of the Failure

Based on `Library/Logs/nightly-review.err` and inspection of the snapshot:

1. **Missing `USER` environment variable in launchd (`Not logged in · Please run /login`)**:
   Under `launchd`, the execution environment is minimal and does not set the `USER` environment variable by default (only `PATH` and `XPC_SERVICE_NAME` were configured in the plist). Without `USER`, `claude` cannot locate or access the user's login credentials/keychain, failing immediately with `Not logged in · Please run /login`.

2. **Assigning to read-only variable `status` in zsh (`/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`)**:
   In `zsh`, `status` is a special read-only built-in variable aliased to `$?`. Attempting to assign `status=$?` immediately aborts the script execution. Because this assignment was placed right after `claude` and before the notification check (`if [ $status -ne 0 ]`), the error handler and failure notification via `notify.sh` never executed.

3. **Multi-line prompt handling in headless/launchd context**:
   Passing multi-line prompt arguments directly to `claude -p "$PROMPT"` under non-interactive launchd environments can cause stdin waiting or prompt truncation issues unless piped via stdin (`print -r -- "$PROMPT" | claude -p ...`) or passed with closed stdin (`< /dev/null`).

---

## 2. Colleague's Note: What Applied vs. What Did Not

### Applied:
- **`status` is a read-only variable in zsh**:
  Directly matched `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`. Assigning to `status` killed the script immediately after `claude` failed, preventing `notify.sh` from sending failure alerts. Replaced with `rc=$?`.
- **Missing `USER` in launchd `EnvironmentVariables`**:
  Matched the log error `Not logged in · Please run /login`. `launchd` runs with a stripped environment where `USER` is not set by default; adding `USER=vk` to `EnvironmentVariables` in `com.vk.nightly-review.plist` allows CLI tools to resolve the user's keychain/credentials.
- **Passing prompt via stdin to `claude -p`**:
  Piping the prompt using `print -r -- "$PROMPT" | claude -p ...` avoids multi-line argument parsing and stdin-blocking issues in scheduled launchd shells.
- **Checking `launchctl print` and log files first**:
  The log files (`Library/Logs/nightly-review.err`) and `launchctl-print.txt` clearly showed `runs = 6`, `last exit code = 1`, and the exact errors that occurred on each run.

### Did Not Apply / Ignored:
- **"Input must be provided either through stdin or as a prompt argument"**:
  In this snapshot, the initial failure was `Not logged in · Please run /login` rather than missing input error, though piping stdin was still applied proactively as recommended for unattended `claude -p` runs.
- **Watchdog / timeout returning exit code 0**:
  The job was exiting with exit code 1 due to the zsh fatal error on `status=$?`.
- **Telegram notifier (`bin/notify.sh`) issues**:
  The colleague's note discussed failure reporting downstream; here `bin/notify.sh` was functional when run directly, but was unreachable due to the script abortion at line 19.

---

## 3. Changes Made

1. **`bin/nightly-review.zsh`**:
   - Changed `status=$?` to `rc=$?` (and updated variable references) so zsh does not abort on a read-only variable assignment.
   - Piped prompt via stdin: `print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"`.

2. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - Added `USER` (`<string>vk</string>`) under `EnvironmentVariables` dict so headless CLI processes can access credentials.
