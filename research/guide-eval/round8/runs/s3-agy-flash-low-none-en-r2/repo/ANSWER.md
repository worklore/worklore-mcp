# Causes of Nightly Job Failure

## Summary
The nightly launchd job (`com.vk.nightly-review`) ran and failed, but failed silently without sending failure notifications to Telegram due to a fatal script error immediately following the Claude CLI invocation.

---

## Root Causes

1. **Failure of Claude CLI invocation (`Not logged in · Please run /login`)**:
   - When executed by launchd, the `claude` command exited with code `1` and printed `Not logged in · Please run /login` to stderr.
   - The CLI authentication session/token was not available or expired in the non-interactive execution environment, causing the command to fail.

2. **Fatal Zsh error on read-only variable assignment (`read-only variable: status`)**:
   - In Zsh, `status` is a built-in special variable that is an alias for `$?` and is read-only.
   - At line 19 of `bin/nightly-review.zsh`, the assignment `status=$?` triggered a fatal shell error:
     ```
     /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
     ```
   - Because of this fatal error, script execution terminated immediately at line 19.
   - As a result, the subsequent error-handling block (lines 21–24):
     ```zsh
     if [ $status -ne 0 ]; then
       "$NOTIFY" "nightly review FAILED (exit $status), see $OUT"
       exit $status
     fi
     ```
     was never reached, preventing `bin/notify.sh` from ever sending a failure alert over Telegram.

---

## Fix Applied
In `bin/nightly-review.zsh`, renamed the variable `status` to `exit_code`:
- Changed `status=$?` to `exit_code=$?`.
- Updated references in the condition and notification message from `$status` to `$exit_code`.

With this fix, whenever `claude` fails (or succeeds), execution continues properly and dispatches the failure notification via Telegram.
