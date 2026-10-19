# Nightly launchd Job Failure Analysis

## Summary of Causes

The nightly launchd job (`com.vk.nightly-review`) ran as scheduled (as evidenced by `runs = 6` in `launchctl-print.txt`), but failed silently due to two stacked issues recorded in `Library/Logs/nightly-review.err`:

1. **Authentication failure due to missing `USER` environment variable in launchd (`Not logged in · Please run /login`)**:
   - `claude` CLI under macOS launchd cannot locate its authentication credentials/tokens in Keychain without the `USER` environment variable set in the launchd job context.
   - In `Library/LaunchAgents/com.vk.nightly-review.plist`, `EnvironmentVariables` only defined `PATH`. Because `USER` was not defined, `claude` failed immediately with exit code 1.

2. **Silent failure due to assigning to the read-only variable `status` in zsh (`read-only variable: status`)**:
   - In `bin/nightly-review.zsh` line 19, the script attempted to capture the return code using `status=$?`.
   - In `zsh`, `status` is a built-in special read-only variable aliased to `$?`. Attempting to assign to `status` causes a fatal error in zsh, terminating script execution immediately.
   - Because this assignment was placed right before the error-handling block (`"$NOTIFY" "nightly review FAILED..."`), the script aborted before the Telegram notification call could ever execute, resulting in complete silence (no summary and no failure notification).

Additionally, when running `claude -p "$PROMPT"` non-interactively without stdin redirected, the CLI can block waiting on stdin in unattended launchd contexts.

---

## Fixes Applied

1. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - Added `<key>USER</key><string>vk</string>` under `EnvironmentVariables` so the headless CLI can access user keychain credentials.

2. **`bin/nightly-review.zsh`**:
   - Replaced assignment to read-only variable `status=$?` with `rc=$?` (and updated subsequent checks to use `$rc`).
   - Closed stdin on `claude` invocation (`< /dev/null`) to prevent stdin blocking in launchd sessions.
