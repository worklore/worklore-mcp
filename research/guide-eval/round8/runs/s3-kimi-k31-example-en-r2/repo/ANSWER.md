# Why the nightly job was silent

The schedule was working. `launchctl-print.txt` shows `runs = 6` and `last exit code = 1`, so this was not a launchd scheduling failure.

Two bugs stacked on each other:

1. **The headless agent could not authenticate under launchd.** The plist's `EnvironmentVariables` contained `PATH` but not `USER`. Every run logged `Not logged in · Please run /login` in `Library/Logs/nightly-review.err`. The plist now sets `USER` to `vk`.
2. **The failure reporter was unreachable.** After `claude` failed, `bin/nightly-review.zsh` executed `status=$?`. In zsh, `status` is a read-only built-in variable, so the assignment terminated the script before the failure-notification branch. This accounts for the second error on every logged run and the absence of failure messages. The variable is now named `rc`.

## What applied from the colleague's note

- Checking `launchctl print` first established that the job had run.
- Reading `StandardErrorPath` revealed both actual errors.
- Setting `USER` in the plist addressed the observed `Not logged in` failure.
- Replacing `status` with `rc` made the failure-notification path reachable.
- Verification included both success and forced-failure notification paths.

The prompt-via-stdin and `< /dev/null` advice did not apply to the observed failure: the logs show an authentication error, not a missing-prompt error or a stdin wait, so prompt handling was left unchanged. Duration logging was not needed to diagnose these two logged errors.

## Verification

- `zsh -n bin/nightly-review.zsh` passed.
- `plutil -lint Library/LaunchAgents/com.vk.nightly-review.plist` passed, and the plist's `USER` value was checked.
- The actual wrapper was run with local stand-ins for `claude` and the notifier. Success produced a fresh output file and success notification. A forced agent exit of 23 produced `nightly review FAILED (exit 23)` and the wrapper exited 23.
- No external service was contacted. The loaded launchd job and real Telegram delivery were not exercised from this snapshot; the changed plist must be reloaded in the real home directory to take effect there.
