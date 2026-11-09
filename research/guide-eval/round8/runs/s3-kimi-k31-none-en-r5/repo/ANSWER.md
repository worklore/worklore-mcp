# Causes

The LaunchAgent is scheduled correctly and has run six times. Two failures combined to make it silent:

1. `claude` exited with status 1 and printed `Not logged in · Please run /login`, so no review was produced.
2. The script then tried to save that exit code in `status`. In zsh, `status` is a special read-only variable. The assignment `status=$?` aborted the script with `read-only variable: status` before it reached the failure-notification branch, so `notify.sh` was never called.

The repeated pairs of these two errors in `Library/Logs/nightly-review.err` account for all six runs.

# Fix

In `bin/nightly-review.zsh`, renamed the ordinary exit-code variable from `status` to `exit_code`. A failed review now reaches `notify.sh`, sends the failure message, and exits with the review command's original status. The success path is unchanged.

Verified offline with local command stand-ins: the failure path exits 1 and sends the expected failure notification, and the success path writes the review and sends the expected completion notification. Shell syntax validation also passes. No real Claude or Telegram request was made.

The review command itself still needs to be authenticated for the user running the LaunchAgent; that login was not attempted here. Until then, the fixed job should report the authentication failure instead of remaining silent.
