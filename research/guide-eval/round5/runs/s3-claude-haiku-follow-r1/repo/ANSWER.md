# Why the nightly review never reported anything

Two bugs, stacked. Together they made the job fail and then made the failure
invisible.

## Evidence

`launchctl-print.txt` (captured 2026-10-18 09:10): `runs = 6`, `last exit code = 1`,
`state = waiting`. The job fired on schedule every night since it was loaded on
2026-10-12. It was not a launchd scheduling problem.

`Library/Logs/nightly-review.err` has six runs, each with the same two lines:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

`nightly-review.out` is empty, so nothing ever reached stdout.

## Cause 1: `claude` could not find the login

The plist sets only `PATH` in `EnvironmentVariables`. Without `USER`, the CLI cannot
find the login in the keychain and exits with "Not logged in". The job fails at
the agent call, before any work is done.

Fix: add `USER` (`vk`) to the plist's `EnvironmentVariables`.

## Cause 2: zsh's read-only `status` killed the failure reporter

`bin/nightly-review.zsh` ran `status=$?` on line 19. In zsh, `status` is a
read-only built-in, so the assignment aborts the script. That line sat between
the agent call and the Telegram failure message, so the script died before
`notify.sh` ran. Nothing was sent. The exit code (1) was the only trace.

Fix: use `rc=$?`, and call the failure notifier first on every failure path.

## Changes

- `Library/LaunchAgents/com.vk.nightly-review.plist`: added
  `USER` = `vk` under `EnvironmentVariables`.
- `bin/nightly-review.zsh`:
  - `status` renamed to `rc`, so the script no longer dies on the assignment.
  - A `fail` helper sends the Telegram failure message before it exits.
  - The prompt goes to `claude -p` on stdin (`print -r -- "$PROMPT" | claude -p ...`)
    rather than as a multi-line argument.
  - Each run logs its start, exit code and duration (`duration=Ns`).
  - Exit 0 with an empty output file is treated as a failure.
  - The success message includes the run duration.

Note: the snapshot shows no "Input must be provided" error, so the prompt-argument
problem was not observed here. The stdin change is hardening, not the fix for
this failure.

## What I verified (locally, with stubs)

I did not run launchd, real `claude` or Telegram. I ran the scripts under
`env -i` with a launchd-like environment (no `USER`, minimal `PATH`, stdin closed),
using a stub `claude` and a stub notifier that writes to a file.

| Scenario | Original script | New script |
|---|---|---|
| `USER` unset (the real plist), claude fails | dies at line 19, **no message** | "claude exit 1" message sent, exit 1 |
| `USER` set, claude fails (exit 3) | dies at line 19, **no message** | "claude exit 3" message sent, exit 1 |
| Success | not run | "done (Ns)" message, exit 0, prompt received on stdin |
| Exit 0, empty output | not run | "empty output" message, exit 1 |
| Repo missing | not run | "repo missing" message, exit 1 |

`zsh -n` passes on the script and `plutil -lint` passes on the plist.

## Not verified here (needs your machine)

- The real `claude` login under launchd with `USER` set.
- The real Telegram send.
- A real run timing (the stub returns in 0 s).

## How to check on your machine

```sh
cp bin/nightly-review.zsh ~/bin/
cp Library/LaunchAgents/com.vk.nightly-review.plist ~/Library/LaunchAgents/
launchctl bootout gui/$UID/com.vk.nightly-review 2>/dev/null
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
tail -5 ~/Library/Logs/nightly-review.out ~/Library/Logs/nightly-review.err
```

Then check:

1. `last exit code = 0`, and `nightly-review-<today>.md` exists and is fresh.
2. The log's `duration=` is a plausible number of seconds for a real review (not ~0 s).
3. You received the "done" message on Telegram.
4. Failure test: `mv ~/projects/shop ~/projects/shop.away`, kickstart again, expect a
   "repo missing" message on Telegram and `last exit code = 1`. Then move the repo back.

Residual risk: if Telegram itself is unreachable, the notifier fails silently. The
only trace is the job's exit code in `launchctl print`, so keep checking `runs`.
