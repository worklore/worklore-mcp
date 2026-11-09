# Why the nightly job was silent

launchd was firing the job. `launchctl-print.txt` records `runs = 6`, the expected 02:30 calendar trigger, and `last exit code = 1`. The corresponding error log contains six repetitions of:

```text
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

There were two causes:

1. **The agent could not use its login under launchd.** The plist's environment contained `PATH` but no `USER`, so the headless CLI could not find its keychain login and printed `Not logged in`. `Library/LaunchAgents/com.vk.nightly-review.plist` now sets `USER` to `vk`.
2. **The wrapper died before either notification path.** In zsh, `status` is a read-only special variable. Assigning `status=$?` terminated the script immediately after the agent call, before both the failure and success notification branches. `bin/nightly-review.zsh` now uses `rc=$?`, and the failure branch reports and exits with `rc`.

The agent prompt remains an argument, so its invocation now also has `< /dev/null`. This prevents the CLI from waiting for standard input in the scheduled context; it was preventive, not a separate error observed in the supplied log.

## Which parts of the colleague's note applied

- Checking `launchctl print` and reading `StandardErrorPath` first applied: they proved the job ran and exposed both errors.
- Replacing `status=$?` with `rc=$?` applied directly.
- Setting `USER` in the plist applied directly to the `Not logged in` failure.
- Closing stdin applied because this script passes the prompt as an argument. The alternative of piping the prompt through stdin did not apply and was not used.
- Forcing a failure to verify notification delivery applied during local verification. No real launchd kickstart or external Telegram request was made.

The note's watchdog/exit-code caveat and duration-logging suggestion were not causes here and did not require changes. The existing script already places its failure notification immediately after capturing the agent result; the fatal assignment was the problem.

## Changes and verification

- `bin/nightly-review.zsh`: renamed the exit-code variable and closed the agent's stdin.
- `Library/LaunchAgents/com.vk.nightly-review.plist`: added `USER=vk`.
- `zsh -n` and `plutil -lint` pass.
- With local agent and notifier stubs, an agent exit of 7 produced `nightly review FAILED (exit 7)` and the wrapper exited 7; a successful agent run created the dated review file containing the mocked summary and produced `nightly review done: fresh review summary`.

The real CLI login, launchd run, and Telegram delivery were not exercised in this snapshot. On the actual Mac, reload the changed plist before the next scheduled run.
