# Why the nightly review stayed silent

The launchd agent did run. The captured `launchctl print` shows six runs and a last exit code of 1; the calendar trigger and script paths were active. `Library/Logs/nightly-review.err` shows the same two errors on each run:

1. `claude` reported `Not logged in · Please run /login`. The launchd job has a minimal environment and cannot rely on an interactive shell's credentials. The job now optionally reads an `ANTHROPIC_API_KEY` from a Keychain item named `nightly-review-anthropic-api-key` before invoking Claude. A usable Claude credential still needs to be placed in that item (or supplied to the agent through its environment); none is present in this snapshot. Until then, the job will report a Claude failure rather than produce a review. On the Mac, `security add-generic-password -U -a "$USER" -s nightly-review-anthropic-api-key -w` prompts for the key without putting it in the command line.
2. In zsh, `status` is a read-only special parameter. The assignment `status=$?` failed before the script reached its failure notification branch. The script now saves the exit code in `review_exit`, so a failed Claude run calls `notify.sh` and exits with that code.

The notifier also discarded Telegram's HTTP response and did not fail on HTTP error codes. It now uses `curl -f` so a rejected request returns a nonzero status, and it logs a clear error if the Telegram token cannot be read from Keychain. Its existing `tg-bot` Keychain item must be readable by the user agent at 02:30 for a Telegram message to arrive.

The changed files are only in this snapshot. They have not been installed into the home directory. After copying them to the corresponding paths and providing the Claude credential, the already loaded agent will use the updated scripts on its next run. Its stdout and stderr are written to `~/Library/Logs/nightly-review.out` and `~/Library/Logs/nightly-review.err`.
