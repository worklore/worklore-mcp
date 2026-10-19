# Why the nightly job was silent

The job **did run**. The captured `launchctl print` shows `runs = 6` and `last exit code = 1`; its 02:30 calendar trigger matches the plist. The stderr log records the same pair of errors six times:

1. `claude` exited immediately with `Not logged in · Please run /login`. The plist supplied `PATH` but no `USER`, which the headless CLI needs to locate the login in the keychain. The plist now sets `USER=vk`.
2. The wrapper then assigned `status=$?`. `status` is read-only in zsh, so the shell stopped before reaching its failure notification. The wrapper now saves the exit code in `rc` and sends a failure message before exiting.

The prompt is now piped to `claude -p` through stdin, avoiding reliance on a multiline prompt argument in the scheduled environment. The script logs each run's duration and treats empty agent output as a failure, so a zero exit code alone cannot report a completed review.

Local verification used a stub `claude` and notifier, with no network calls: a successful review sent a success message and exited 0; an agent exit of 7 sent a failure message and exited 7; empty output sent a failure message and exited 1. Each run printed a duration. The plist parsed and the zsh script passed syntax checking.

This snapshot is not the installed agent, so it has not been reloaded or kicked off. After copying the fixes to the real home directory, reload the plist and run `launchctl kickstart -k gui/$UID/com.vk.nightly-review`. Check its new exit code, stderr, duration, fresh review file, and Telegram success message. Force an agent failure once and confirm the failure message arrives too.
