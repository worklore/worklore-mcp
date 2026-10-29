# Why the nightly review was silent

The launchd agent **did run**. The captured `launchctl print` shows six runs and a last exit code of 1. Its 02:30 calendar trigger and paths are present, so the evidence does not point to a scheduling or PATH failure.

Two failures are visible in `Library/Logs/nightly-review.err` on every run:

1. `claude -p` prints `Not logged in · Please run /login`. The headless CLI has no usable authentication in the account running this agent, so it cannot produce a review. This still needs to be resolved on the actual Mac: sign in to Claude CLI as the same user that owns the LaunchAgent, and ensure that authentication is available to a noninteractive launchd process. The snapshot cannot supply or validate account credentials.
2. Immediately afterward, `nightly-review.zsh` assigns to `status`, a read-only special variable in zsh. That aborts the script before its failure-notification branch. I renamed it to `review_status`, so a failed review now reaches `notify.sh` and retains the CLI exit code. The failure message now points to `nightly-review.err`, where the CLI error is logged, instead of the empty review output file.

The empty `nightly-review.out` is expected: the script redirects Claude's standard output to a dated Markdown file and `notify.sh` discards the Telegram response. I also made `notify.sh` use `curl -f`, so an HTTP error from Telegram produces a nonzero exit and a launchd stderr entry instead of being treated as a successful send.

After the Claude login is fixed, the script can send summaries. Until then, it should send a failure note **if** the launchd process can read the `tg-bot` Keychain item and reach Telegram. The snapshot proves neither of those conditions for launchd; a successful manual notifier run does not establish them. If notifications remain absent after this script fix is installed locally, inspect `Library/Logs/nightly-review.err` for `security` or `curl` errors and make the Keychain item accessible to this user agent. No live Telegram request or launchd deployment was made during this fix.
