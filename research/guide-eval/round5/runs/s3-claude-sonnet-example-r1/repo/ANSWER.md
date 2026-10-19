# Why nightly-review was silent

Evidence: `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`, so the job fired every night (schedule 02:30). It was failing, and the failure reporter was dead. `Library/Logs/nightly-review.err` shows both causes, repeated 6 times.

## Causes
1. **`claude -p` was "Not logged in"** under launchd. The plist's `EnvironmentVariables` has no `USER`, so the CLI can't find its login in the keychain. This is the original failure.
2. **`status=$?` in `bin/nightly-review.zsh` (line 19)**. `status` is a read-only zsh variable, so the script died right there (`read-only variable: status`), before the `notify.sh` failure call. The job failed and then killed its own messenger. That is why no failure note ever arrived.

Contributing: `notify.sh` uses `set -e`, and its result was never checked, so a notifier failure would also be silent. The `claude` call had no closed stdin, and a run that exited 0 with an empty output file would have been reported as success.

## Fixes
- Script: `rc=$?` instead of `status=$?`; `< /dev/null` on the `claude` call; log rc and duration to stderr; treat an empty output file as a failure; notifier failures are logged and the script exits non-zero.
- Plist: added `USER` (`vk`) to `EnvironmentVariables`.

## Colleague's note: what applied
- Applied: check `launchctl print` first (runs/exit code); read the stderr log; the read-only `status` variable in zsh (use `rc`); `USER` in the plist; `< /dev/null` with an argument prompt; log duration; the exit code isn't proof of success, so check the output.
- Did not apply: piping the prompt over stdin. Here the prompt reached `claude` fine; the error was "Not logged in", not a missing-input error. The note's 16:50 schedule and "no evidence it ran" also don't match this case (02:30, and the logs exist).

## To do on your machine (not verifiable here)
Copy the files back to `~`, then `launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist` (the plist change needs a reload), then `launchctl kickstart -k gui/$UID/com.vk.nightly-review`. Confirm exit code 0, a fresh non-empty `nightly-review-<date>.md`, a plausible duration in the `.err` log, and the Telegram message. Then force a failure once (e.g. temporarily rename the repo) to confirm the failure note arrives. If "Not logged in" persists, the keychain may be unavailable to the background session; run `claude` `/login` in a GUI session. Also check that `notify.sh`'s `security find-generic-password` works under launchd.
