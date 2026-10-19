# Why the nightly job was silent

The job **did run**. The captured `launchctl print` shows six runs and `last exit code = 1`. Its stderr log repeats the same two errors for each run:

1. `Not logged in · Please run /login`: `claude` failed before producing a review. The plist supplied `PATH` but not `USER`; the unattended CLI needs the account name to find its login. The fix adds `USER=vk` to the LaunchAgent environment. The log proves the login failure; the missing `USER` is the likely configuration cause, supported by the existing troubleshooting note in this snapshot.
2. `read-only variable: status`: after `claude` failed, `nightly-review.zsh` assigned its exit code to zsh's read-only `status` parameter. That terminated the script before it reached the failure notification. The fix uses `rc` instead, so a failed agent run sends a failure message and retains the agent's exit code.

The script now closes stdin for the noninteractive `claude -p` call and treats empty output as a failure. These guard against other silent outcomes; neither was demonstrated by the captured log. There is no evidence here that the calendar trigger failed or that Telegram itself failed.

## Verification and activation

`plutil -lint` and `zsh -n` pass. Local stand-ins for `claude` and `notify.sh` produced a success message on success, a failure message with exit code 7 when the agent failed, and failure messages for empty output and a missing repository. No external service was contacted.

Only this snapshot was edited. The live LaunchAgent must be reloaded after these files are copied into the real home directory, because a loaded launchd job does not pick up plist environment changes automatically. A real run is still needed to confirm the CLI login and Telegram delivery in that environment.
