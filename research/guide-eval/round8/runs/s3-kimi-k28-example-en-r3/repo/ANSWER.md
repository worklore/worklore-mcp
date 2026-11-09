# Why the nightly review was silent

The job was never broken the way it looked ("launchd isn't firing"). It fired
every night, failed every night, and its failure reporter died before it could
say so. Two stacked bugs, each independently sufficient for silence:

## Cause 1 — the job failed every run: no `USER` in the launchd environment

The plist's `EnvironmentVariables` set only `PATH`, so when launchd ran the
script, `claude` could not resolve the user's keychain login and exited
immediately with:

```
Not logged in · Please run /login
```

Evidence: `Library/Logs/nightly-review.err` lines 1, 3, 5, … — once per run,
6 times. `launchctl-print.txt` confirms `runs = 6` and `last exit code = 1`.

## Cause 2 — the messenger was killed: `status=$?` in zsh

`bin/nightly-review.zsh:19` assigned the agent's exit code to a variable named
`status`. In zsh, `status` is a read-only special variable (an alias of `$?`);
assigning to it aborts the script on the spot. That line sat between the agent
call and the failure notification, so every night the sequence was: agent
fails → script dies at line 19 → the `if` block that calls `notify.sh` never
executes. Nothing on Telegram, ever.

Evidence: `nightly-review.err` lines 2, 4, 6, … — `read-only variable: status`,
once per run. Reproduced directly: `zsh -c 'true; status=$?; echo hi'` prints
the same error and exits 1 without ever reaching `echo`.

## Fixes applied

- `bin/nightly-review.zsh` — `status=$?` → `rc=$?` (the kill-switch is gone; the
  failure notification now fires immediately after the agent call, with the
  real exit code preserved).
- `bin/nightly-review.zsh` — the multi-line prompt is now piped to the agent
  via stdin (`print -r -- "$PROMPT" | claude -p …`) instead of being passed as a
  `-p` argument, so it can't be mangled by argument parsing or leave the agent
  waiting on stdin under launchd.
- `bin/nightly-review.zsh` — each run now logs its outcome and duration to
  stdout (lands in `nightly-review.out` via the plist), so a too-fast run is
  visible instead of silent.
- `Library/LaunchAgents/com.vk.nightly-review.plist` — added `USER` = `vk` to
  `EnvironmentVariables`, so the agent CLI can find its keychain login.

## What the colleague's note did for this case

Applied, in order:

- **`launchctl print gui/$UID/<label>` first** — `launchctl-print.txt` showed
  `runs = 6`, `last exit code = 1`, `state = waiting`: the job had been firing
  on schedule all along. This re-framed the whole problem from "not running" to
  "failing and unable to report".
- **Read the StandardErrorPath log before theorizing** — `nightly-review.err`
  named both bugs outright; no theorizing was needed.
- **In zsh never assign to `status`, use `rc=$?`** — exactly Cause 2.
- **Pass the prompt via stdin rather than as a multi-line argument** — adopted.
- **Set `USER` in `EnvironmentVariables` or the CLI dies with "Not logged in"** —
  exactly Cause 1 (the note's 2026-09-30 correction, which matched the observed
  error verbatim).
- **Log each run's duration** — adopted.
- **Force a failure once and confirm the failure notification arrives** —
  done, with mocks (see below).

Not applied / noted instead:

- The `< /dev/null` variant for prompt-as-argument was superseded by the
  stdin-pipe approach (one fix covers both traps).
- The correction that runs count / exit code "do not lie" is taken seriously:
  the exit code here proves the script ran, not that it worked — so the script
  now also logs duration, and the real outcome is the `$OUT` file plus the
  Telegram message, which should be checked fresh after each run.

## Verification (and its limits)

Verified in a sandboxed fake `$HOME` with a mock `claude` and a mock
`notify.sh` (no real agent calls, no Telegram messages sent):

- Original script + failing agent → both error lines, exit 1, **zero**
  notifications (silence reproduced exactly).
- Fixed script + failing agent → failure notification sent, exit 1, duration
  logged.
- Fixed script + succeeding agent → success notification sent, exit 0, review
  written to `$OUT`, and the agent received the full multi-line prompt intact
  on stdin.
- Repo-missing path → notification sent, exit 1.
- `zsh -n` and `plutil -lint` both pass.

Not verifiable from this snapshot: a real `launchctl kickstart` and a real
Telegram delivery. After copying the two fixed files into the real home dir,
reload and force a run:

```
launchctl bootout gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
```

Then confirm `launchctl print` shows `last exit code = 0`, a fresh
`~/Library/Logs/nightly-review-$(date +%F).md` with real content, a plausible
run duration (not a few seconds), and the Telegram summary.

One residual risk to eyeball during that test: `bin/notify.sh` runs with
`set -eu` and reads its token via `security find-generic-password`; if that
lookup ever fails under launchd, the notifier itself dies without a sound. It
worked by hand per the README, but the forced-failure test above should be
watched once to confirm it also works under launchd.
