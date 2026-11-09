# Causes

The LaunchAgent was scheduled and executed: `launchctl-print.txt` records six runs and a last exit code of 1. Two separate problems explain the missing reviews and notifications.

1. **The coding agent was not authenticated.** Every captured run begins with `Not logged in · Please run /login` in `Library/Logs/nightly-review.err`, so `claude` did not produce a review.
2. **The error handler crashed before it could notify.** After `claude` exited, `bin/nightly-review.zsh` ran `status=$?`. In zsh, `status` is a read-only special variable. The assignment failed (`read-only variable: status` on line 19 in the captured log), terminating the script before either the failure or success call to `notify.sh`. This is why no failure note was sent.

# Fix

`bin/nightly-review.zsh` now stores `$?` in `exit_code` instead of `status` and uses that variable in the failure branch. The branch therefore sends the failure notification and exits with the agent's original exit code.

Local tests with stubbed agent and notifier commands confirmed both paths: an agent exit of 23 produced `nightly review FAILED (exit 23)` and returned 23; a successful agent run produced the summary notification. Shell syntax checks and `plutil -lint` also passed. No external service was contacted.

This fixes notification delivery control flow, but it does not authenticate `claude`. Until the user logs in in the launchd job's user context, real nightly runs should now send failure notes rather than reviews.
