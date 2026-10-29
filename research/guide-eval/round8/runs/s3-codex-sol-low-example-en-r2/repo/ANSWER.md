# Why the nightly job was silent

The job **did run**. The captured `launchctl print` shows six runs and `last exit code = 1`. Its stderr log repeats the same two errors six times:

1. `claude` exited with `Not logged in · Please run /login`. The launchd plist provided `PATH` but no `USER`; the headless CLI needs the login name to locate its keychain credentials. I added `USER=vk` to `EnvironmentVariables`.
2. Immediately afterward, the wrapper tried `status=$?`. In zsh, `status` is read-only. That error stopped the wrapper before its failure notification, so Telegram received nothing. I replaced it with an `if` around the agent command and capture its exit code as `rc` on failure.

The wrapper now closes the agent's stdin when passing the prompt as an argument, treats an empty response as a failure, and logs run duration and output location. The existing notifier is still used for both outcomes. The successful response must be nonempty before a success notice is sent.

## Colleague's note

Applied: check `launchctl print` and stderr before assuming the schedule never fired; avoid zsh's read-only `status`; set `USER` in launchd; close stdin for an argument-based `claude -p` call; check the real output as well as the exit code; log duration.

Did not apply: the prompt was already supplied as a quoted argument, and the log shows an authentication error, not a missing-prompt error. Piping the prompt into stdin was therefore unnecessary here. The snapshot also cannot prove that a real Telegram notification arrived or that a live agent review succeeded.

## Verification

`zsh -n bin/nightly-review.zsh` and `plutil -lint Library/LaunchAgents/com.vk.nightly-review.plist` pass. This is a home-directory snapshot, so no live launchd job was reloaded or kicked off and no Telegram message was sent. After installing the changed files in the real home directory, reload the agent and run it once. Check its new summary file, stderr duration, launchd exit code, and both success and forced-failure notifications.
