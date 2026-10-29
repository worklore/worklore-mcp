# Why the nightly review was silent

The scheduler ran. The saved `launchctl print` shows six runs and a last exit code of 1. `Library/Logs/nightly-review.err` contains six pairs of errors: `Not logged in · Please run /login`, then `read-only variable: status` at line 19 of the wrapper. The zero-byte stdout log was not evidence that launchd failed to start the job; the errors went to stderr.

There were two linked causes:

1. The launchd environment had `PATH` but no `USER`. The headless `claude` invocation could not find its login in that environment. The repeated `Not logged in` message is direct evidence of the CLI failure; missing `USER` is the likely environment cause identified by the colleague's note. The snapshot cannot prove whether the installed CLI also needs its credentials refreshed.
2. After `claude` failed, the zsh script tried `status=$?`. `status` is read-only in zsh, so the script stopped before its failure notification. This directly explains why no Telegram failure note arrived.

## Changes

- The plist now sets `USER=vk` and `HOME=/Users/vk` explicitly for the scheduled process.
- The wrapper uses `rc` for the exit code, closes the CLI's stdin when passing the prompt as an argument, logs the CLI exit code and elapsed time, and sends a failure notice if the CLI exits unsuccessfully or returns an empty output file. A nonempty successful result still sends the summary.

## Which parts of the colleague's note applied

- **Applied:** Check `launchctl print` and the stderr log first; launchd did run. The read-only zsh `status` assignment killed the failure reporter. Set `USER` in the launchd environment. Close stdin when using `claude -p` with a prompt argument. Record duration and check the real output, since an exit code alone does not prove a review was produced.
- **Did not apply:** This script already supplied the prompt as an argument, and the log contains no “Input must be provided” error. Piping the prompt through stdin is therefore not the fix for this case. The colleague's 16:50 schedule and claim about a missing log are unrelated; this job is scheduled for 02:30 and its stderr log exists.

## Verification and limit

`plutil -lint` accepted the edited plist and `zsh -n` accepted the wrapper. Local stand-ins for `claude` and the notifier confirmed all three paths: a nonempty result exits 0 and sends a success message; CLI exit 7 sends a failure message and exits 7; empty output with CLI exit 0 sends a failure message and exits 1. The stand-in also checked that stdin was closed. No live launchd job, Claude login, repository review, or Telegram delivery was exercised from this snapshot.
