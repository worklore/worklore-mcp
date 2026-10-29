# Why nightly-review never reported anything

## It did run
`launchctl-print.txt` (captured 2026-10-18) shows `runs = 6` and `last exit code = 1`.
Loaded 2026-10-12, so that's one run per night from the 13th to the 18th. launchd was fine.
The script failed every night and couldn't tell you. `Library/Logs/nightly-review.err`
has the same two lines six times:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

## Cause 1: `claude` is "Not logged in" under launchd
The plist's `EnvironmentVariables` set only `PATH`. launchd doesn't set `USER` for
the job (look at the `environment` block in the print: just PATH and XPC_SERVICE_NAME).
Without `USER` the CLI can't find its login in the keychain, so it exits 1 straight
away. The review never started, and `nightly-review-<date>.md` was created empty.

**Fix:** added `USER` = `vk` to `EnvironmentVariables` in
`Library/LaunchAgents/com.vk.nightly-review.plist`.

## Cause 2: `status=$?` kills the script before it can send the failure note
This one is why you heard nothing. In zsh, `status` is a read-only special variable.
Assigning to it is a fatal error in a non-interactive script, so zsh exits with code 1
at line 19. That line comes before the `if` that calls `notify.sh`, so the failure
message was never sent. A success message wouldn't have been sent either: the script
dies on that line every time, whatever `claude` returns.
Reproduced: `zsh -c 'false; status=$?; echo reached'` prints
`read-only variable: status` and never prints `reached`.

**Fix:** use `rc=$?`.

## Other hardening in `bin/nightly-review.zsh`
- The prompt goes to `claude -p` on stdin (`print -r -- "$PROMPT" | claude -p ...`),
  so there's no multi-line argument and no risk of it waiting on stdin.
- `claude`'s stderr goes to a per-day `.err` file, and its first 300 characters
  are included in the failure message. You'd have seen "Not logged in" on your phone.
- It logs the start time, `USER`, the exit code and how long the run took. A run
  that takes a few seconds means it failed before doing any work.
- Exit 0 with an empty output file now counts as a failure and sends a notification.
- If `notify.sh` itself fails, that's written to the stderr log instead of disappearing.

Tested with stubbed `claude`/`notify.sh` (outside this folder). A forced failure
sends a FAILED message with the error text. Exit 0 with empty output sends a FAILED
message. A normal run sends the summary.

## Which parts of the colleague's note applied
- **Applied:** prove it ran with `launchctl print` (runs / last exit code). Read the
  stderr log before theorizing. The `status` read-only variable killing the messenger:
  same bug, same line. Set `USER` in the plist for "Not logged in": that's our first
  error. Log the duration and don't trust exit 0 alone. Test the failure path on purpose.
- **Applied as hardening, not a cause here:** pipe the prompt on stdin. Your log
  shows a login error, not "Input must be provided...". launchd already gives jobs
  a /dev/null stdin, so the `< /dev/null` advice didn't apply either.
- **Not applicable:** the 16:50 schedule and the watchdog-exits-0 example.

## To do on the real machine (not done here; this is a snapshot)
1. Copy the two files into place, then reload:
   `launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`
2. `launchctl kickstart -k gui/$UID/com.vk.nightly-review`. Then check that
   `last exit code = 0`, that today's `nightly-review-<date>.md` is non-empty,
   that the run took a plausible time in `nightly-review.err`, and that a Telegram
   message arrived.
3. Force a failure once (for example, temporarily point `REPO` at a missing directory)
   and confirm the failure note arrives.
4. If `claude` still says "Not logged in" with `USER` set, run `claude` once
   interactively to log in. If `notify.sh` fails under launchd (it reads the bot
   token from the keychain with `security`), the stderr log will now say so.
