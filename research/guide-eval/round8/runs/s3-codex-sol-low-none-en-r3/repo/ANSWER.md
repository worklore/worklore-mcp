# Why the nightly review stayed silent

The agent is loaded and its calendar trigger is firing: `launchctl-print.txt` records six runs, each with exit code 1. The stderr log shows the same two errors on every run.

1. `claude -p` reports `Not logged in · Please run /login`. The headless job has no usable Claude authentication, so it cannot produce a review. Authentication must be configured for the `vk` account in the environment where this launch agent runs; the snapshot contains no credential with which to do that.
2. Immediately after that failure, `nightly-review.zsh` assigned `$?` to `status`. In zsh, `status` is a read-only special parameter. That assignment aborted the script before its failure notification, explaining why no failure note arrived.

The script now branches directly on the `claude` exit result, stores a failure code in `review_exit`, and calls the notifier on either outcome. Failure notes point to the stderr log, where the actual error is recorded. `notify.sh` now makes HTTP error responses from Telegram fail visibly in the job log instead of silently accepting them.

To get summaries, complete Claude authentication for the launch agent's user and verify that its noninteractive `claude -p` invocation succeeds. The code fix allows a failure note to be attempted meanwhile, provided the Telegram token is available to the agent's keychain lookup and Telegram is reachable. No live credentials or external services were used while making this change.
