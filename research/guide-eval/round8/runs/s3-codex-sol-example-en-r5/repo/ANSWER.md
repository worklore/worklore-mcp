# Why the nightly review was silent

The job **did run**. The captured `launchctl print` shows six runs and a last exit code of 1. Its stderr log repeats the same pair of errors six times:

1. `claude` exited with `Not logged in · Please run /login`. The plist supplied `PATH` but omitted `USER`, which the headless CLI needs to find the login in the macOS keychain. I added `USER=vk` to `EnvironmentVariables`.
2. Immediately afterward, the wrapper assigned `status=$?`. `status` is read-only in zsh, so the script stopped before its failure notification. I changed this to `rc=$?` and kept the notification on the failure path.

The wrapper now closes stdin when passing the prompt as an argument, logs each run's duration, reports empty agent output as a failure, and logs notification failures. The notifier now makes `curl` fail on HTTP errors. These changes help reveal later failures; the two errors above explain the six silent runs in this snapshot.

## Colleague's note

**Applied:** Check the `launchctl` run count and stderr; avoid zsh's read-only `status`; set `USER` in the plist; close stdin for an argument-based `claude -p` call; record duration; and test the failure notification path.

**Did not apply:** The note's missing-prompt diagnosis. This script already passed a prompt argument, and its log shows an authentication error instead. Piping the prompt through stdin was therefore unnecessary. The note's reported run count, schedule, and job label were from a different job.

## Verification and remaining check

The plist passes `plutil -lint`, and both scripts pass shell syntax checks. With local stubs, the wrapper sent a success note on a nonempty result, sent failure notes for agent exit 7 and empty output, and exited nonzero when the notifier failed. These tests made no external requests.

This directory is a snapshot, so the installed agent was not reloaded or run. After installing the changed files on the Mac, reload the LaunchAgent, run it once, and check the fresh output file and notification along with `launchctl print` and the logs. The snapshot cannot prove that the keychain login remains available at run time or that Telegram accepts the message.
