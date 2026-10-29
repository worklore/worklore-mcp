# Why the nightly review never reports anything

## Cause 1 (the one that stops every run): `status` is a read-only variable in zsh

`bin/nightly-review.zsh` line 19 was `status=$?`. In zsh, `status` is a read-only
special parameter (an alias for the last exit status), so the assignment fails:

```
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

The script aborts there, before it reaches either `$NOTIFY` call. So no success
message and no failure message is ever sent, and the job exits 1. That is why
the launchd job shows `last exit code = 1` and why Telegram stays silent.

Evidence:
- `Library/Logs/nightly-review.err` contains that exact error on every run.
- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`.
- Reproduced locally with zsh 5.9: `status=$?` aborts the script with exit 1, and
  `rc=$?` works.

Fix: renamed the variable to `rc` in `bin/nightly-review.zsh`, with a comment
explaining why.

## Cause 2: the job runs logged out

Under launchd the job's `claude -p` call fails with:

```
Not logged in · Please run /login
```

This is the second failure. Fixing Cause 1 alone would only bring this one to
light. The snapshot doesn't show why the credentials are missing for the launchd
job, but the likely reason is that a launchd agent does not inherit your
interactive shell's environment (for example an API key or config-dir variable
exported in `~/.zshrc`). I could not verify this from here.

What I changed: stderr now goes to a per-day `.err` file, and the failure
notification includes its first 300 characters. The next failed run will tell
you "Not logged in · Please run /login" on your phone instead of nothing.

What you need to do: make the job's credentials explicit, for example by
generating a long-lived token with `claude setup-token` (check `claude --help`
for the exact subcommand) and loading it from the Keychain, the same way
`notify.sh` loads `tg-bot`. I did not add any token to the repo.

## Cause 3: the notifier fails silently

`bin/notify.sh` could report success even when it had failed:

1. If the Keychain lookup for `tg-bot` failed, `TG_BOT_TOKEN` was empty. The
   script then POSTed to `https://api.telegram.org/bot/sendMessage` and still
   exited 0. I reproduced this with a stub `curl`.
2. `curl -sS` without `-f` does not treat HTTP errors (bad token, 404, 401) as
   failures, and its output went to `/dev/null`.

So even a working job would have had no way to report that Telegram rejected the
message.

Fix: `notify.sh` now exits 1 with a message on stderr when the token is empty,
and uses `curl -f`, so HTTP errors fail the script.

## Not changed, but likely to bite next

- **Headless permissions.** `claude -p` cannot ask for tool permission. If the
  review needs `git log` or `git show` and those aren't pre-approved, the review
  may come back thin or with denied-tool notes. I did not change this, because I
  can't verify it from the snapshot. If it happens, add read-only
  `--allowedTools` entries (for example `Bash(git log:*)` and `Bash(git show:*)`)
  to the `claude` call.
- **Keychain access under launchd.** `notify.sh` reads the token with
  `security find-generic-password`. That should work in the GUI session, but it
  can't be checked from the snapshot. The new error message will say so if it
  fails.
- **Stray error line.** The `.err` file has seven "Not logged in" entries and
  `runs = 6`. The extra one is probably a manual run.

## What I verified

Everything was tested locally with a throwaway HOME and stub `claude`/`curl` on
PATH. I did not run the real job, call Claude, or send anything to Telegram.

- Logged-out run: exit 1, and the failure message contains the auth error.
- Success run: exit 0, and the summary is sent.
- Telegram HTTP error: the job exits non-zero instead of 0.
- No token: `notify.sh` exits 1 with a clear message and does not call curl.
- `zsh -n` and `bash -n` pass on both scripts.

## Files changed

- `bin/nightly-review.zsh`: `status` renamed to `rc`; stderr captured in a
  per-day `.err` file and included in the failure message.
- `bin/notify.sh`: empty-token check; `curl -f`.
- `ANSWER.md`: this file.
