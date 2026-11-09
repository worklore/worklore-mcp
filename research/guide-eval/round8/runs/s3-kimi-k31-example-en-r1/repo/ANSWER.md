# Why the nightly job was silent

Launchd was not the problem. `launchctl-print.txt` records `runs = 6` and `last exit code = 1`, and `Library/Logs/nightly-review.err` contains the same two errors six times:

1. **The headless agent could not authenticate under launchd.** Each run began with `Not logged in · Please run /login`. The plist supplied `PATH` but not `USER`, so the CLI could not find its login in the keychain. I added `USER=vk` under `EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`.
2. **The failure reporter was killed before it could run.** After the agent failed, `bin/nightly-review.zsh` executed `status=$?`. In zsh, `status` is a read-only special variable; assigning to it terminates the script. Because this happened before the `if` that calls `notify.sh`, neither failure nor success notifications could be sent. I renamed the variable to `rc` and preserved the original agent exit code.

I also changed the agent invocation to use `< /dev/null`. The prompt is already an argument; closing stdin prevents the CLI from waiting for input in launchd's noninteractive context. This was preventive hardening, not an error observed in the supplied log.

`notify.sh` was not the cause of the original silence: execution never reached it after the agent failure.

# Which parts of the colleague's note applied

- **Applied:** prove that launchd ran the job with `launchctl print`; read `StandardErrorPath`; replace the zsh `status` assignment with `rc`; set `USER` in the plist; close stdin when passing the prompt as an argument; exercise both success and forced-failure notification paths.
- **Not applicable:** piping the prompt through stdin (this script already passes it as an argument), and diagnosing a multi-line prompt parsing failure (the observed agent error was authentication).
- **Not needed for this fix:** adding duration logging or relocating the notification call; once the fatal assignment was removed, the existing failure branch was reachable.
- **Not performed:** live `launchctl kickstart`, real Claude authentication, or Telegram delivery. This is only a home-directory snapshot, and the task prohibits deployment and external reporting.

# Changes and verification

Changed `bin/nightly-review.zsh` and `Library/LaunchAgents/com.vk.nightly-review.plist` as described above.

Using local stand-ins for `claude` and `notify.sh`, with no network calls, I verified that:

- a successful agent run creates a nonempty review and calls the success notifier;
- a forced agent exit of 7 calls the failure notifier with exit 7 and makes the wrapper exit 7;
- the agent receives `/dev/null` as stdin;
- both scripts pass shell syntax checks, the plist passes `plutil -lint`, its `USER` value is `vk`, and `git diff --check` passes.

The snapshot is fixed and locally tested; the loaded launchd agent has not been changed or run.
