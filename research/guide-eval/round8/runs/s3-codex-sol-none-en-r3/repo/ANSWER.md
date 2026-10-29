# Why the nightly job reported nothing

The launch agent **did run**. `launchctl-print.txt` shows six runs, a calendar trigger at 02:30, and a last exit code of 1. The six matching entries in `Library/Logs/nightly-review.err` show what happened on each run:

1. `claude -p` failed with `Not logged in · Please run /login`. The headless launchd process does not have usable Claude authentication, so it cannot produce a review. The snapshot contains no credentials to restore that access. Authenticate the CLI for the same user and environment in which the agent runs, or provide its supported noninteractive credentials securely, then verify a headless `claude -p` invocation succeeds.
2. Immediately after that failure, `nightly-review.zsh` assigned the exit code to `status`. In zsh, `status` is a read-only special parameter. The resulting error terminated the script before it could call `notify.sh`, so even the failure note was never sent. The script now captures the exit code in `claude_status` and sends the failure note. It also treats an empty CLI response as a failure.

`nightly-review.out` being empty is expected here: the CLI output is redirected to a dated `nightly-review-YYYY-MM-DD.md` file, and the errors went to `nightly-review.err`. The configured PATH includes the usual Homebrew locations; the log shows the CLI was found and ran.

`notify.sh` now reports a missing keychain token and makes `curl` return an error for HTTP failures. Its working when called manually does not prove that the 02:30 launchd process can access the keychain. Once Claude authentication is fixed, verify that the job can read the `tg-bot` item and deliver a test message in its launchd context. No job was launched and no external message was sent from this snapshot.
