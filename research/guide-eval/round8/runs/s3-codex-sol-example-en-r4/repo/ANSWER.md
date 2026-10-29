# Why the nightly review was silent

The job **did run**. The captured `launchctl print` shows `runs = 6` and `last exit code = 1`. The stderr log contains six pairs of errors:

1. `Not logged in · Please run /login` from Claude. The loaded job's environment has no `USER`, and the plist did not set it. This is consistent with the headless CLI failing to find its login. The snapshot proves the authentication failure; it cannot prove that adding `USER` alone restores the login on the live Mac.
2. `read-only variable: status` at line 19 of the zsh wrapper. `status=$?` terminates the wrapper before its failure notification. This explains why even the failure was never reported.

The wrapper now uses `rc`, and the plist supplies `USER=vk`. The Claude call has closed stdin, records its duration and exit code, and treats empty output as failure. The notifier now makes HTTP errors fail visibly with `curl -f`.

## Colleague's note

- **Applies:** Check the run count and stderr before assuming launchd did not fire; avoid assigning to zsh's read-only `status`; set `USER` for the headless CLI; close stdin when passing the prompt as an argument; check the actual output as well as the exit code; record run duration and exercise the failure notification.
- **Does not apply:** The prompt was already supplied as a single quoted `-p` argument, and the observed Claude error was authentication, not “Input must be provided.” Piping the prompt through stdin is unnecessary here. The captured exit code was `1`, so this case was not a false green exit.

## Verification and limit

`zsh -n`, `bash -n`, and `plutil -lint` pass. Local mocks of Claude and the notifier confirmed that a successful review sends a success message, Claude exit 7 sends a failure message and exits 7, and empty output sends a failure message and exits 1. The mock read all of stdin, confirming the call does not wait for input. No live Claude, Telegram, or launchd job was run from this snapshot. The modified plist must be loaded on the real Mac before its new environment takes effect; then a real run should confirm Claude can authenticate and that Telegram receives the summary.
