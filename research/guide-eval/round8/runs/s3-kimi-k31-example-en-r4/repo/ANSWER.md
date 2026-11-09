# Why the nightly job was silent

The job was running; it was not a launchd scheduling failure. `launchctl-print.txt` records `runs = 6` and `last exit code = 1`, and `Library/Logs/nightly-review.err` contains the same two errors for every run.

Two bugs combined to hide every failure:

1. **The headless agent could not authenticate.** The plist's `EnvironmentVariables` set only `PATH`, so launchd did not provide `USER`. The agent consequently failed with `Not logged in · Please run /login` before producing a review. Fixed by setting `USER` to `vk` in `Library/LaunchAgents/com.vk.nightly-review.plist`.
2. **The wrapper died before its failure notifier.** After the agent failed, `bin/nightly-review.zsh` executed `status=$?`. In zsh, `status` is a read-only built-in variable; assigning to it terminates the script. The script therefore never reached the branch that calls `notify.sh`. Fixed by using `rc=$?` and using `rc` in the failure branch.

The first bug caused the nightly failure, and the second prevented that failure from being reported. Successful runs would still have used the existing success notifier.

# What applied from the colleague's note

Applied:

- Checking `launchctl print` first established that the job had run and exited unsuccessfully.
- Reading `StandardErrorPath` revealed both actual errors.
- Adding `USER` under `EnvironmentVariables` addressed the observed `Not logged in` failure.
- Replacing the zsh `status` assignment with `rc` restored the failure-notification path.
- Testing both success and forced failure confirmed that notifications are now attempted in both directions.

Not applied, because the logs did not implicate them:

- Switching the prompt to stdin or adding `< /dev/null`: the prompt is already passed as one quoted argument, and the observed failure was authentication, not argument parsing or waiting for stdin.
- Adding duration logging or moving the notifier: neither was needed to fix the two demonstrated faults.

# Verification

- `plutil -lint Library/LaunchAgents/com.vk.nightly-review.plist` passed.
- `zsh -n bin/nightly-review.zsh` passed.
- With local stubs and an isolated `HOME`, the full wrapper sent a success notification after a simulated successful review.
- With the agent stub forced to exit 42, the full wrapper sent the failure notification and exited 42.

No live agent, Telegram request, launchd reload, or external service was used. The plist must be reloaded in the real home directory for the environment change to affect future scheduled runs.
