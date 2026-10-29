# Why the nightly review never reports anything

The job runs (launchctl shows `runs = 6`, `last exit code = 1`), but it never
reaches the point where it sends a message. Three things combine.

## Cause 1: the script crashes on `status=$?` (fixed)

`bin/nightly-review.zsh` stored the exit code in a variable named `status`.
In zsh, `status` is a read-only special parameter (another name for `$?`), so
the assignment fails:

```
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

With `set -u` the script exits with status 1 right there. The failure branch
and the success branch both come after that line, so no Telegram message is
sent either way. This is the error that appears six times in
`Library/Logs/nightly-review.err`.

Fix: the variable is now `rc`, and the claude call is `claude ... || rc=$?`.
The `||` keeps `set -u` from tripping on a failing command.

## Cause 2: `claude -p` is not logged in under launchd (not fixed, needs you)

Every run in `nightly-review.err` begins with:

```
Not logged in · Please run /login
```

Your interactive shell is logged in, but the LaunchAgent is not getting that
login. I can't see your keychain or credentials from this snapshot, so I
haven't changed auth. Options:

1. Run `claude setup-token` in a terminal and store the token you get in the
   login keychain. Then have the job export `CLAUDE_CODE_OAUTH_TOKEN` from
   it, the same way `notify.sh` reads `tg-bot`.
2. Or export `ANTHROPIC_API_KEY` in the plist's `EnvironmentVariables`. That
   stores a secret in a plist, so option 1 is better.

Then check it by hand under launchd, not in your shell:
`launchctl kickstart -k gui/$(id -u)/com.vk.nightly-review`, then read
`Library/Logs/nightly-review.err`.

## Cause 3: failures in `notify.sh` were silent (fixed)

`bin/notify.sh` filled the token with `$(security ... -w)` and never checked
it. If the keychain lookup failed, the token was empty, the request went to
`/bot/sendMessage`, and curl (without `-f`) reported success on the HTTP 404.
Errors were swallowed, so a broken notifier looks the same as no job at all.

Fix: the script stops with a message on stderr when the token is empty, and
curl uses `-f` so HTTP errors become a non-zero exit.

## What changed

- `bin/nightly-review.zsh`: `status` renamed to `rc`; the failure notice now
  points at `nightly-review.err` as well.
- `bin/notify.sh`: token check and `curl -f`.

Verified with stubs (a failing `claude`, a succeeding `claude`, and a missing
token). The scripts pass `zsh -n` / `bash -n`. Nothing was deployed. Copy the
two files to `~/bin/` to put them in place. Cause 2 still needs your credentials.
