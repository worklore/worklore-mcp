# Why the nightly review was silent

The job **did run**. The captured `launchctl print` shows six runs, a 02:30 calendar trigger, and `last exit code = 1`. The stderr log has the same two errors six times: `claude` says `Not logged in · Please run /login`, then zsh says `read-only variable: status` at line 19 of the wrapper. The empty stdout log is expected because the wrapper redirects the agent's stdout to a dated summary file.

The agent failed before producing a review. The plist supplied `PATH` but no `USER`; that is a plausible cause of the headless CLI being unable to locate its saved login. The snapshot cannot prove that adding `USER` is sufficient: the real Mac may also need a valid CLI login or keychain access. The immediate reason **no failure note arrived** is certain: `status=$?` assigns to zsh's read-only `status` parameter and terminates the wrapper before its notification branch. This would also have killed the wrapper after a successful agent call, so no success note could have been sent either.

## Fixes in this snapshot

- Set `USER=vk` in the launchd plist, matching the account in the captured paths.
- Use `rc` for the agent exit code. Send the failure note as soon as an agent failure is detected.
- Close stdin for `claude -p` because the prompt is already passed as an argument.
- Treat a zero-exit, empty summary as a failure. Log the run duration and notification outcome to stderr so a fast or silent run is diagnosable.
- Make the Telegram notifier fail visibly when keychain lookup or the HTTP request fails; the wrapper logs a notifier failure and exits nonzero.

The colleague's **runs/exit-code check**, **read-only `status` bug**, **`USER` setting**, **closed stdin for an argument prompt**, **duration logging**, and **checking the real output rather than only exit 0** apply here. Their **missing prompt** diagnosis does not: this wrapper already passes the prompt as an argument, and its recorded error is an authentication error. Piping the prompt through stdin is therefore unnecessary here. Their `launchctl kickstart` and real success/failure notification checks remain useful after deployment, but were not run against this snapshot.

## Verification and remaining live check

`zsh -n`, `bash -n`, and `plutil -lint` pass. Local mock runs exercised success, agent exit 7, empty output, and notifier exit 1: the wrapper returned 0, 7, 1, and 1 respectively; failure cases produced failure messages when the mock notifier worked, and the notifier failure appeared in stderr. These tests did not contact Telegram or the real agent.

This directory is a snapshot, so the edited plist and scripts have **not** been installed or reloaded in the real user's launchd session. After applying them there, reload the agent so the new `USER` environment takes effect, run it once, and check a fresh nonempty summary file, the stderr duration, and an actual Telegram message. If `Not logged in` persists, repair the CLI login/keychain access in that account. Then force one agent failure and confirm the failure message arrives.
