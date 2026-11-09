# Why the nightly job never reported anything

The job itself was fine — `launchctl print` shows it ran every night
(`runs = 6`, one per night since bootstrap). Every run died silently because of
two stacked problems, both visible in `Library/Logs/nightly-review.err`, which
contains the same two lines repeated once per run:

## Cause 1 — the script aborted before it could send a failure note

`bin/nightly-review.zsh:19: read-only variable: status`

`status` is a reserved, read-only special variable in zsh (an alias for `$?`).
The script does `status=$?` after running claude; zsh rejects the assignment
and, in a non-interactive script, treats it as a fatal error: the shell exits
with status 1 immediately. The `if [ $status -ne 0 ]` branch that calls
`bin/notify.sh` is never reached.

So even though claude failed every single night, the code that was supposed to
tell you about it never executed. This is the direct reason you received
nothing — no summary and no failure note. It is also why `last exit code = 1`
in the launchctl dump: the exit status comes from zsh's complaint about the
bad assignment, not from anything meaningful.

Reproduced in the sandbox with the original script + a claude stub that fails:
exit 1, `read-only variable: status`, notifier never invoked — byte-for-byte
the behavior in your `.err` file.

**Fix:** renamed the variable to `rc` in `bin/nightly-review.zsh`.

## Cause 2 — claude is not logged in when launched by launchd

`Not logged in · Please run /login`

The claude CLI does start under launchd (it's in `/opt/homebrew/bin`, which is
on the job's PATH), but it finds no usable credentials. Your interactive login
doesn't carry over to the launchd-spawned process (macOS keychain / session
credentials aren't reachable from there), so every run failed before doing any
review. This is the "works in my terminal, not from launchd" credential
problem.

This one I cannot fully fix from a snapshot: the standard remedy is a
non-interactive token for the headless job, which requires your Anthropic
account. The script now supports it cleanly:

1. Run `claude setup-token` in your terminal and copy the token.
2. Create `~/.config/nightly-review.env` (mode 600) containing:
   ```
   export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-...
   ```
   (or `export ANTHROPIC_API_KEY=...`).
3. Done — `bin/nightly-review.zsh` sources that file if present. I deliberately
   did not put the token in the plist: `launchctl print gui/501/...` shows a
   job's environment variables in plaintext, and editing the plist would also
   require a `bootout`/`bootstrap` cycle.

Until you add the token, the job will at least now *report* its failure every
night instead of going silent (verified: with the fix, a failing claude run
produces `nightly review FAILED (exit 1), see ...` via notify.sh; with a token
present, the full summary is sent).

## Related hardening (not a confirmed cause)

`bin/notify.sh` reads the Telegram bot token with
`security find-generic-password -s tg-bot -w`. Whether that works from a
launchd-spawned process depends on keychain state/ACLs, and it has never
actually been exercised under launchd (the script always died before calling
it). It works from your terminal, which is a good sign. I made the failure
mode explicit: if the keychain read ever fails, notify.sh now writes
`notify.sh: could not read the 'tg-bot' item from the keychain` to
`nightly-review.err` and exits 1, instead of dying quietly under `set -eu`.
If you *do* get the failure note from Cause 2's fix but summaries still never
arrive, the `tg-bot` keychain item's access settings are the next thing to
check.

## Verified

Sandbox end-to-end runs of the fixed script with a fake `$HOME`, stub `claude`
and stub notifier (no network, nothing external):

- failing claude, no token → Telegram path invoked with `nightly review FAILED (exit 1)...`, exit 1
- working claude + token file → Telegram path invoked with `nightly review done: ...`, exit 0, dated report written to `~/Library/Logs/`
- unreadable keychain item → clear error on stderr, exit 1
