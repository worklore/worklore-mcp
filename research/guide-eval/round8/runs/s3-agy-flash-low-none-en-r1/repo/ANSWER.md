# Nightly Review Job Failure Analysis

## Summary of Causes

The launchd job failed and never reported anything (not even a failure notification) due to two distinct causes:

1. **Failure to notify / Script fatal crash (`status` is a read-only variable in Zsh)**:
   - In `bin/nightly-review.zsh` at line 19, the script attempts to assign `status=$?`.
   - In Zsh, `status` is a built-in special variable that aliases `$?` and is **read-only**.
   - Attempting to assign `status=$?` throws a fatal error: `read-only variable: status`, terminating execution immediately before `if [ $status -ne 0 ]` and before calling `bin/notify.sh`.
   - This fatal crash prevented any failure notification from being sent to Telegram.

2. **Underlying failure cause (`claude` authentication in launchd environment)**:
   - When launched by `launchd`, user agents execute in a clean environment lacking standard interactive session variables unless explicitly set.
   - Specifically, `USER` (and `HOME`) are not populated in the daemon's environment table. Claude Code uses `process.env.USER` to identify keychain credentials (`Claude Code-credentials` under the user's account name). Without `USER`, Claude Code cannot locate credentials in Keychain and outputs `Not logged in · Please run /login` with exit code 1.
   - When `claude` failed with exit code 1, the script proceeded to line 19 to handle the error, where Cause 1 was triggered, completely silencing the alert.

---

## Fix Applied

In [`bin/nightly-review.zsh`](file:///tmp/h-eGbZXn/bin/nightly-review.zsh#L18-L24):
- Renamed variable `status` to `exit_code` to avoid clashing with Zsh's built-in read-only `$status` parameter:
  ```zsh
  claude -p "$PROMPT" --output-format text > "$OUT"
  exit_code=$?

  if [ $exit_code -ne 0 ]; then
    "$NOTIFY" "nightly review FAILED (exit $exit_code), see $OUT"
    exit $exit_code
  fi
  ```
