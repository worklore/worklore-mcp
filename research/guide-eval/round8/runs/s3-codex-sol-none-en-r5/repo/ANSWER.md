# Why the nightly review was silent

The launchd schedule is working. The captured `launchctl print` shows six runs and a last exit code of 1; the error log records the same two errors on each run.

1. `claude` exits with `Not logged in · Please run /login`. It has no usable authentication in this launchd job's environment, so it cannot produce a review. The snapshot does not show why its credentials are unavailable.
2. Immediately afterward, the zsh script assigns to `status`, a read-only zsh parameter. That terminates the script before its failure notification. This is why even the authentication failure was never reported to Telegram.

I changed `bin/nightly-review.zsh` to capture the command's exit code in `review_exit` and send the failure notification. To restore summaries, authenticate `claude` for the user and environment that runs this LaunchAgent (the CLI error requests `/login`), then verify that a noninteractive `claude -p` run can use those credentials. This snapshot contains no credentials, and none were added to the plist or repository.

Verification: `zsh -n` and `plutil -lint` pass. A local stub run returned exit 1 and recorded the failure notification for a simulated login error; a successful stub run recorded the summary notification. No Claude or Telegram service was contacted.
