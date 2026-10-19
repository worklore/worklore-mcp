# Why the nightly job was silent

The job **did run**. The captured `launchctl print` shows `runs = 6` and `last exit code = 1`. Its stderr log has six repetitions of the same two errors, while stdout is empty.

1. `claude` exited with `Not logged in · Please run /login`. The launchd environment shown in the snapshot has no `USER`, although the login user is `vk`. The plist now supplies `USER=vk` so the headless CLI can locate that user's login credentials. This diagnosis is supported by the error and missing environment variable; the snapshot cannot prove that credentials are currently valid.
2. Immediately after `claude` failed, the wrapper assigned to `status`, a read-only zsh parameter. That terminated the script before its failure notification. The wrapper now uses `rc` and sends the failure message before exiting with the original code.

The wrapper also closes stdin when passing the prompt as an argument, treats empty agent output as a failure, and makes the notifier fail on an HTTP error. These guard against additional silent or false-success cases; the snapshot does not show that they caused the six recorded failures.

## Colleague's note

Applied: inspect `launchctl print` and stderr; avoid zsh's `status` variable; set `USER` for the headless CLI; close stdin when `claude -p` receives a prompt argument; check the real output rather than relying only on the exit code.

Did not apply: the note's missing-prompt error is absent here. This script already passes its multiline prompt as one quoted argument, so there is no evidence that piping the prompt via stdin is needed. Its suggested run-duration logging and live `kickstart` checks cannot establish the cause from this offline snapshot.

## Verification

`zsh -n`, `bash -n`, and `plutil -lint` pass. With local mock commands, a failed agent run sent a failure notification and returned its exit code, an empty successful run sent a failure notification, and a run with output sent a success notification. No live launchd job or Telegram delivery was tested from this snapshot.
