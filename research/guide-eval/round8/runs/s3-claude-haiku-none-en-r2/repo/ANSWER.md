# Why the nightly-review job never reports anything

Evidence: `launchctl-print.txt` (runs = 6, last exit code = 1), and
`Library/Logs/nightly-review.err`, which has six identical pairs of lines,
one per night:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

`nightly-review.out` is empty, as expected, because the summary goes to a
separate `nightly-review-DATE.md` file.

## Cause 1 (the one that hides everything): `status` is read-only in zsh

`bin/nightly-review.zsh` ran `status=$?`. In zsh, `status` is a read-only
special parameter (a synonym for `$?`). The assignment fails with
`read-only variable: status`, and in a non-interactive shell that error
aborts the script on that line. So:

- the failure branch (`if [ $status -ne 0 ]` → `notify.sh "... FAILED"`) is never reached;
- the success notification is never sent either;
- the job exits with status 1, which is the `last exit code = 1` in launchd.

The failure is therefore silent in Telegram, and the only trace is the `.err`
file. I reproduced this with a stub `claude` that exits 1: the script printed
the read-only error, exited 1, and sent nothing.

**Fix:** renamed the variable to `rc` in `bin/nightly-review.zsh`, with a
comment explaining why.

## Cause 2: the job itself cannot log in to Claude

The six runs that got past the job's start show `Not logged in · Please run
/login`. launchd gives the job `claude` on PATH (the plist sets it), so the
binary runs. It is the credentials that are missing in this context. The
snapshot does not show exactly why (a likely candidate is that the login
credentials are only readable from an interactive session; I could not verify
that from these files), so this part is not fixed by a code change.

Ways to check and fix it on your Mac:

1. Trigger a run by hand and read the error log:
   `launchctl kickstart gui/$(id -u)/com.vk.nightly-review` then
   `cat ~/Library/Logs/nightly-review.err`.
2. Long-lived token: run `claude setup-token` in Terminal, store the token in
   the keychain (`security add-generic-password -s claude-oauth -a "$USER" -w`),
   and export `CLAUDE_CODE_OAUTH_TOKEN` from the keychain in the script before
   `claude -p`. Keep the token out of the plist and out of git.

With Cause 1 fixed, a failure like this now reaches Telegram as
`nightly review FAILED (exit 1): Not logged in ...`, so you will see it the next
night even before the auth is fixed.

## Cause 3: `notify.sh` could fail silently

`bin/notify.sh` read the token with `: "${TG_BOT_TOKEN:=$(security ...)}"`. If
the keychain lookup fails (locked keychain, missing item, or no access from
launchd), the assignment does not stop the script, because `:` succeeds. The
token is then empty, the URL is `.../bot/sendMessage`, Telegram answers 404,
and `curl -sS` without `-f` treats that as success and prints nothing. So even
a working job could report nothing. I reproduced the empty-token case.

**Fix:** `bin/notify.sh` now exits 1 with a message on stderr when the token
cannot be read, and uses `curl -f` so HTTP errors fail.

## Not a cause

The schedule is fine: `StartCalendarInterval` 02:30 is loaded, the plist is
valid XML, the paths in the plist point to the right files, and the job has run
every night since loading (six runs for 12–17 Oct).

## Changes made

- `bin/nightly-review.zsh`: `status` → `rc`; claude's stderr goes to
  `$OUT.err`, and the failure note includes its first 300 bytes.
- `bin/notify.sh`: explicit token check; `curl -f`.

Tested with stub `claude` and `security` commands in a scratch directory (since
removed): failing claude → failure note with the reason; succeeding claude →
"done" note; missing token → exit 1 with a message. I did not send any real
Telegram message or call the real Claude service.

Not yet done, and needs you: the auth fix in Cause 2, and a real
`launchctl kickstart` on your Mac to confirm the end-to-end result.
