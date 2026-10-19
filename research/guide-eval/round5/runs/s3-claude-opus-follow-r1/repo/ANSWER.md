# Why com.vk.nightly-review never reported anything

## First: it did run

`launchctl-print.txt` shows `runs = 6` and `last exit code = 1`. Six runs is
one per night from 2026-10-13 to 2026-10-18 (it was loaded on 2026-10-12), so
launchd was firing on schedule. The script was failing every night, and
`Library/Logs/nightly-review.err` has the same two lines six times:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

## Cause 1: `claude` is "Not logged in" under launchd

The job's environment holds only `PATH` and `XPC_SERVICE_NAME` (see the
`environment` block in `launchctl print`). `USER` isn't set, so the `claude`
CLI can't find its login in the keychain and exits 1 straight away. The
review never started, which is why `nightly-review.out` and the `.md` output
are empty.

**Fix:** `USER` (plus `LOGNAME` and `HOME`) are now set under
`EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`.

## Cause 2: `status=$?` killed the script before it could report the failure

This is why nothing ever reached Telegram. In zsh, `status` is a read-only
special parameter (the same thing as `$?`). Assigning to it is a fatal error,
so the script died on line 19. That line sits between the `claude` call and
the `"$NOTIFY" "nightly review FAILED ..."` call, so the failure reporter was
downstream of the failure and never ran. `notify.sh` itself was never called.

**Fix:** the script now uses `rc=$?`. It also has a `TRAPEXIT` that sends a
failure note whenever the script exits non-zero for a reason it didn't
already report, so an unexpected zsh error can't make it silent again.

## Other hardening in `bin/nightly-review.zsh`

- The prompt now goes to `claude -p` on stdin
  (`print -r -- "$PROMPT" | claude -p ...`) instead of as a multi-line
  argument. This also means `claude` can't hang waiting on stdin.
- A zero exit code alone no longer counts as success. The run is reported as
  failed if the output file is empty or if `claude` finished in under 10
  seconds, which in practice means it died before doing any work.
- Each run writes its start time, the `claude` exit code and the duration to
  the `.err` log. The duration is also included in the Telegram message.
- If sending the summary fails, that is reported as a failure too.

## Tested locally (stubs, no launchd, no network)

I ran the script with stub `claude` and `notify.sh` in a scratch home.
Each of these cases sent the expected message:

| Case | Result |
|---|---|
| `claude` exits 1 ("Not logged in") | FAILED note, exit 1 |
| `claude` exits 0 with no output | FAILED note, exit 1 |
| `claude` exits 0 with output in 0 s | FAILED note, exit 1 |
| `claude` reads the prompt from stdin, takes 10 s | "done" note with the summary, exit 0 |
| Script with `status=$?` put back in | trap sends "script died" note, exit 1 |

`plutil -lint` passes on the plist and `zsh -n` passes on the script.

## What you need to do on the real machine

Nothing has been deployed. Copy the files into place, then reload the agent so
the new environment variables take effect:

```sh
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
```

Check all of the following:

- `last exit code = 0`.
- `~/Library/Logs/nightly-review-<today>.md` exists and has content.
- The `.err` log shows a plausible duration, not a few seconds.
- The "done" Telegram message arrived.

Then break the script on purpose once (for example, point `REPO` at a missing
directory) and confirm the FAILED message arrives too.

If it still says "Not logged in", run `claude` once interactively to log in.
Also check that `security find-generic-password -s tg-bot -w` works under
launchd (`notify.sh` uses it), or set `TG_BOT_TOKEN` in the plist.
