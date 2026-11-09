# Causes

1. **The coding agent was not logged in.** Every recorded run in `Library/Logs/nightly-review.err` begins with `Not logged in · Please run /login`, so `claude -p` exited with an error instead of producing a review. The six copies match the six runs reported by launchd.

2. **A zsh-specific variable name aborted the script before it could notify.** In zsh, `status` is a read-only special parameter containing the last command's exit status. Consequently, the assignment `status=$?` failed with `read-only variable: status`. This happened after both successful and failing agent runs, so execution never reached either call to `notify.sh`. This—not Telegram or the notifier—explains why there were no failure messages.

The launchd calendar trigger and configured `PATH` were working: launchd ran the job six times and was able to execute `claude`.

# Fix

In `bin/nightly-review.zsh`, replaced the reserved variable `status` with `exit_code`. Agent failures now reach the existing failure-notification branch, and successful runs can reach the success notification.

The agent still needs to be authenticated on the actual Mac as the user running the launch agent: run `claude` as `vk` and complete `/login`. No credentials are present in this snapshot, and no external service was contacted. Until that one-time setup is done, the fixed script should send a failure note rather than remain silent.

The script's failure and success paths were exercised locally with mock `claude` and notifier commands; both produced the expected notifications. Shell syntax and the launchd plist also passed validation.
