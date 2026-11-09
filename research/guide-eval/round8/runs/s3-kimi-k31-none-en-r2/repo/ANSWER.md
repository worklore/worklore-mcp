# Why the nightly job was silent

There were two failures, one after the other:

1. **The review agent was not authenticated.** Every recorded run printed `Not logged in · Please run /login` in `Library/Logs/nightly-review.err`, so `claude` exited unsuccessfully and no review summary was produced.
2. **The failure handler crashed before it could notify.** In zsh, `status` is a read-only special variable containing the previous command's exit status. The assignment `status=$?` therefore failed with `read-only variable: status`. Because a non-interactive zsh aborts on that error, execution never reached the branch that calls `notify.sh`. This explains the missing failure messages as well as the missing summaries.

The launchd schedule itself was working: `launchctl-print.txt` shows six runs and a last exit code of 1. The notifier was never reached after the agent failures.

# Fix

`bin/nightly-review.zsh` now saves the agent's exit status in `exit_code` instead of `status`, then uses that variable for the failure notification and exit. Local tests with stand-ins for both Claude and the notifier verified that:

- an agent failure sends the failure message and preserves its exit code;
- an agent success sends the summary message and saves the review output.

No external service was contacted. Successful reviews still require Claude to be authenticated in the launchd user's environment (for example, through its normal interactive `/login` setup); that login is not present in this snapshot and was not attempted here.
