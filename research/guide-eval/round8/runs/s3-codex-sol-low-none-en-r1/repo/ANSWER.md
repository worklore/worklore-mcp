# Why the nightly job sent nothing

The agent is loaded and its calendar trigger has fired: `launchctl-print.txt` records six runs and a last exit code of 1. The error log shows the same two errors on each run.

1. `claude -p` fails with `Not logged in · Please run /login`. The job has no usable Claude authentication in its launchd session, so it cannot produce a review. Authentication must be set up for the account and noninteractive environment that actually runs the job; no credential is present in this snapshot, so that part cannot be completed here.
2. Immediately after that failure, the zsh script assigns `$?` to `status`. In zsh, `status` is a read-only special parameter. The assignment aborts the script before the failure branch can call `notify.sh`. This is why even the failure note never arrives. I changed the variable to `review_exit`.

After configuring Claude authentication on the real machine, run the job from its launchd context and check `Library/Logs/nightly-review.err` if it still fails. The Telegram notifier also needs access to its `tg-bot` Keychain item in that context; this snapshot contains no evidence that it has failed, because the script never reached it.
