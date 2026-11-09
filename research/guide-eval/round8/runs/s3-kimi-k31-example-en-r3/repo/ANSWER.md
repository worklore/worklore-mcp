# Why the nightly job was silent

The schedule was working. `launchctl-print.txt` records six runs and a last exit code of 1. `Library/Logs/nightly-review.err` contains the same two errors for every run:

1. **The headless agent could not access its login.** The plist's `EnvironmentVariables` contained only `PATH`, not `USER`. In this launchd context, Claude reported `Not logged in · Please run /login`.
2. **The wrapper died before either notification path.** `bin/nightly-review.zsh` assigned the agent's exit code to `status`, which is a read-only special variable in zsh. The unconditional assignment terminated the script with `read-only variable: status`, before the failure branch could call `notify.sh`. It would also prevent a success notification after a successful agent run.

There was a third launchd trap in the agent invocation: the prompt was passed as an argument but stdin was left open. A headless `claude -p` invocation can wait for stdin in that situation. This is not needed to explain the six logged failures, but it was unsafe and has been fixed.

# Fixes

- Added `USER=vk` to `Library/LaunchAgents/com.vk.nightly-review.plist` so the headless CLI can find its keychain login.
- Replaced `status` with `rc` in `bin/nightly-review.zsh`, preserving the agent's exit code and allowing both notification paths to run.
- Added `< /dev/null` to `claude -p` so its argument-supplied prompt does not leave it waiting on stdin.

# What applied from the colleague's note

Applied: checking `launchctl print` before assuming a scheduling problem; reading `StandardErrorPath`; replacing zsh's read-only `status` with `rc`; setting `USER` in the plist; closing stdin for an argument-supplied prompt; and testing both success and forced failure while checking the actual output file and notifications.

Not applied: piping the prompt through stdin, because closing stdin is the appropriate alternative for the existing argument-based invocation; adding duration logging or restructuring the notification path, because neither was needed for these fixes.

# Verification

The plist and both scripts passed syntax validation. The real wrapper was run locally with stand-ins for Claude and the notifier, without contacting any external service. The success run produced the review and success notification; the forced failure returned exit 23 and produced the corresponding failure notification. The agent stand-in also confirmed immediate EOF on stdin.

The snapshot was not deployed, and no live `launchctl kickstart` or Telegram delivery was attempted. After installing these files in the home directory, reload or kickstart the LaunchAgent and confirm a real notification.
