# Causes of Failure and Fixes

## Why the nightly job never reported anything

The job experienced two stacked failures that caused complete silence:

1. **Missing `USER` environment variable in launchd configuration (`Library/LaunchAgents/com.vk.nightly-review.plist`)**:
   - `launchd` executes user agents in a minimal environment (`PATH`, `XPC_SERVICE_NAME`), omitting standard login environment variables such as `USER`.
   - When the headless CLI (`claude`) runs without `USER` defined in its environment, it cannot locate credentials in the macOS keychain and fails immediately with:
     ```
     Not logged in · Please run /login
     ```
   - This caused `claude -p` to exit with an error code on every run.

2. **Assigning to read-only variable `status` in zsh (`bin/nightly-review.zsh`)**:
   - Immediately following the `claude` command, the script attempted to capture the exit code using `status=$?`.
   - In zsh, `status` is a special built-in variable that aliases `$?` and is strictly read-only.
   - Attempting to assign to `status` causes zsh to terminate immediately with a fatal error:
     ```
     /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
     ```
   - Because this assignment was located before the error-handling block (`if [ $status -ne 0 ]; then "$NOTIFY" ...`), the script crashed before it could call the notification messenger (`bin/notify.sh`). Both the success and failure notification paths were blocked.

---

## Colleague Note: Which Parts Applied

From the colleague's note:

- **Applied:**
  - **Read `StandardErrorPath` first**: Checking `Library/Logs/nightly-review.err` confirmed the exact two errors: `"Not logged in · Please run /login"` and `"/Users/vk/bin/nightly-review.zsh:19: read-only variable: status"`.
  - **`status` assignment bug in zsh**: Assigning to `status` in zsh killed the script before reaching notification reporting. Replaced `status=$?` with `rc=$?`.
  - **Missing `USER` in `EnvironmentVariables`**: Under `launchd`, headless CLI keychain access fails without `USER`. Added `<key>USER</key><string>vk</string>` to `com.vk.nightly-review.plist`.
  - **Closing stdin (`< /dev/null`)**: Added `< /dev/null` to the `claude -p` call in `bin/nightly-review.zsh` to prevent hanging or stdin-waiting behavior in headless non-interactive environments.

- **Did Not Apply:**
  - **Prompt passing failure ("Input must be provided either through stdin or as a prompt argument")**: In this job, `claude` was already invoked with `-p "$PROMPT"`, and the primary CLI failure was the keychain authentication error caused by missing `USER`, not argument parsing.

---

## Fixes Implemented

1. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - Added `USER` (`vk`) to `EnvironmentVariables`.

2. **`bin/nightly-review.zsh`**:
   - Replaced `status=$?` with `rc=$?` (and updated variable references in the check and notification message).
   - Added `< /dev/null` to `claude -p "$PROMPT" --output-format text > "$OUT"` to prevent stdin stalls under launchd.
