# Why the nightly job was silent

There were two failures in sequence:

1. **Claude was not authenticated in the launchd environment.** Every recorded run ends with `Not logged in · Please run /login` in `Library/Logs/nightly-review.err`. Consequently, `claude -p` exited unsuccessfully and produced no review summary.
2. **The failure handler crashed before it could notify.** `bin/nightly-review.zsh` assigned the command's exit code to `status`, but `status` is a read-only special variable in zsh. The resulting `read-only variable: status` error aborted the script before it could call `notify.sh`. This is also recorded after every authentication error in `nightly-review.err` and explains why there were no failure messages.

# Fix

Replaced `status` with `exit_code` in `bin/nightly-review.zsh`. The script now preserves Claude's exit code, sends the failure notification, and exits with that code. Local mocked tests confirmed both the failure-notification and successful-summary paths without contacting any external service.

Successful reviews still require a one-time interactive Claude login as the same macOS user that runs the agent (run `claude`, then use `/login`). That authentication was not attempted here because it requires an external service. Until then, the repaired script will send a failure note instead of remaining silent.
