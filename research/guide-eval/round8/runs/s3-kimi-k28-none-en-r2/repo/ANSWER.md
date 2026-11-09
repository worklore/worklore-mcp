# Why the nightly job never reported anything

There are two independent bugs. Together they explain the total silence.

## Cause 1 — the failure handler crashes before it can notify (the silence)

`status` is a **read-only special variable in zsh** (an alias of `$?`). Line 19 of
`bin/nightly-review.zsh` did:

```zsh
status=$?
```

The moment `claude` exits non-zero, this assignment aborts the whole script with
`read-only variable: status` and exit code 1 — before the `if` that calls
`notify.sh` is ever reached. So the "nightly review FAILED" message could never
be sent. (This works in bash, which is presumably why it looked fine in review.)

Evidence:

- `Library/Logs/nightly-review.err` is 6 identical pairs of lines:
  `Not logged in · Please run /login` followed by
  `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`.
- `launchctl-print.txt` shows `runs = 6`, `last exit code = 1` — one run per
  night since load (2026-10-12 → 2026-10-18), each dying the same way.
- Reproduced locally: with a stubbed `claude` (exit 1) and stubbed `notify.sh`,
  the original script exits 1 without calling the notifier; the fixed script
  sends the failure note.

**Fixed:** renamed `status` → `rc` in `bin/nightly-review.zsh:18-24`.

## Cause 2 — `claude` is not authenticated in the launchd context (why no summaries)

Every run, `claude` printed `Not logged in · Please run /login` to stderr and
exited non-zero. Its credentials are reachable from the interactive Terminal
session but not from the process launchd spawns (Claude Code's auth is stored in
the login keychain / session-bound storage, which a `gui/$UID` LaunchAgent
cannot access the same way).

Cause 1 was masking this: it is why you got *no* message. Cause 2 is why the
message you would have received was a failure note, and why even with cause 1
fixed the job will only send "FAILED" notes until claude is authenticated for
headless use. This cannot be fixed from this snapshot (it requires your real
credentials); to fix it on the machine:

- Preferred: store credentials where the agent can read them without the
  keychain — run `CLAUDE_CODE_USE_KEYCHAIN=0 claude /login` once, or set
  `ANTHROPIC_API_KEY` in the plist's `EnvironmentVariables`.
- Then verify with `launchctl kickstart -k gui/$UID/com.vk.nightly-review`
  and check Telegram and `~/Library/Logs/nightly-review.err`.

## Worth verifying once the above is fixed

`bin/notify.sh` reads the bot token via `security find-generic-password -s tg-bot -w`.
That keychain read has the same potential launchd visibility issue as claude's
auth (it works by hand per the README, but the job never got far enough to
exercise it under launchd). The kickstart test above will confirm; if it fails,
store the token in a `chmod 600` file and read that instead of the keychain.
