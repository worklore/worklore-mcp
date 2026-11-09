# Why the nightly review was silent — and what fixed it

## Short answer

The job ran fine. It failed every night, and then the code that was supposed to
report the failure crashed before it could speak. Two stacked bugs, plus one
latent trap defused along the way:

1. **The agent call failed under launchd** — every run died with
   `Not logged in · Please run /login` because the job's environment had no
   `USER`, so the headless CLI could not reach its keychain login.
2. **`status=$?` killed the script before it could notify** — in zsh, `status`
   is a read-only special variable, so the assignment at the old line 19 was a
   fatal error. The failure-notification call sat *after* that line and never
   ran. This is the layer that turned "failing every night" into "total
   silence".

## Evidence

`launchctl-print.txt` (captured 2026-10-18, job loaded 2026-10-12):

- `runs = 6` — the job fired on schedule every night; it was never a
  scheduling problem.
- `last exit code = 1` — it failed every time.
- `environment` shows only `PATH` (plus `XPC_SERVICE_NAME`) — **no `USER`**.

`Library/Logs/nightly-review.err` — 12 lines, six identical pairs, one pair
per run (12–18 Oct is exactly six 02:30 firings after the 2026-10-12 load):

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

Line 1 of each pair is claude exiting "Not logged in" (that message goes to
stderr, which is why `> "$OUT"` never captured anything and the log the user
was sure didn't exist had the answer all along). Line 2 of each pair is the
script dying on `status=$?` — one line before the `if` that would have sent
the failure note. So: no summaries because the agent never succeeded, and no
failure notes because the messenger was killed between the failure and the
report. Perfect silence, two layers deep.

## Fixes applied

`bin/nightly-review.zsh`:

- `status=$?` → `rc=$?` (never assign to `status` in zsh). The failure branch
  is now reachable, so a failing run sends "nightly review FAILED (exit N …)".
- The prompt is now piped to the agent via stdin
  (`print -r -- "$PROMPT" | claude -p --output-format text`) instead of being
  passed as a multi-line argument. This also removes the risk of the headless
  call blocking on an inherited stdin under launchd (see the note's `<
  /dev/null` trap — piping the prompt makes it moot).
- Added per-run duration logging (`SECONDS`) to both notifications, and the
  failure note now points at both the run's `.md` file and the `.err` log,
  since the real error text lives in the latter.
- The `cd`-failure notification was already correctly placed and is unchanged.

`Library/LaunchAgents/com.vk.nightly-review.plist`:

- Added `USER=vk` to `EnvironmentVariables`, next to `PATH`, so the headless
  CLI can find its keychain login.

## Verification (inside the snapshot only)

`zsh -n` passes; `plutil -lint` passes. Then I rebuilt the launchd conditions
in a scratch HOME (`env -i PATH=<plist PATH> HOME=… USER=vk /bin/zsh …`) with
fake `claude`/`notify.sh` (no Telegram calls, per ground rules):

- **Original script + failing agent** → exit 1, stderr reproduces the exact
  two lines from the real `.err` log, **0 notifications sent**. Bug reproduced.
- **Fixed script + failing agent** → exit 1, failure notification **sent**,
  naming the exit code, duration, and both logs.
- **Fixed script + working agent** → exit 0, success notification sent with
  the review head; the fake agent confirmed it received the prompt via stdin;
  the dated `.md` output file was created.

On the real machine, after copying the fixed files into place:
`launchctl bootout gui/$UID/com.vk.nightly-review` then
`launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`,
then `launchctl kickstart -k gui/$UID/com.vk.nightly-review` and confirm with
`launchctl print` that the exit code is 0, the dated `.md` file is fresh, the
run took a plausible amount of time, and the Telegram summary arrives. Also
force one failure (e.g. temporarily rename `~/projects/shop`) and confirm the
failure note arrives — silence should now be impossible in both directions.
The Telegram token lookup in `bin/notify.sh`
(`security find-generic-password -s tg-bot`) worked by hand before and should
keep working in the gui/501 session now that `USER` is set, but it could not
be exercised from this snapshot — worth one real kickstart to confirm.

## Which parts of the colleague's note applied

Applied, nearly verbatim:

- **"First prove whether it ran."** `launchctl print` showed `runs = 6`,
  `last exit code = 1` — the premise "it never ran" was wrong before I started.
- **"Read the StandardErrorPath log before theorizing."** The `.err` log
  contained the exact answer; the user just hadn't looked (they believed no
  log existed).
- **"In zsh, never assign to `status` — use `rc=$?`."** This was the silence
  layer: our line 19 was byte-for-byte their bug, and the notifier was
  downstream of the fatal line, exactly their "check whether your failure
  reporter is downstream of the failure."
- **"Set `USER` under `EnvironmentVariables` … or the CLI dies with 'Not
  logged in'."** This was the failure layer: our plist set only `PATH` and the
  log said exactly "Not logged in · Please run /login."
- **Prompt delivery via stdin / the `< /dev/null` trap.** We passed the prompt
  as a multi-line argument; the note's primary fix (pipe it via
  `print -r -- "$PROMPT" | claude -p`) was adopted, which also closes the
  hangs-on-stdin trap without needing `< /dev/null`.
- **"Log each run's duration" and the verify protocol** (kickstart, then
  confirm exit code 0 *and* a fresh real outcome *and* a plausible duration,
  plus one forced failure to test the failure path) — adopted in the script
  (`SECONDS` in both messages) and in the verification steps above.
- **"Put the failure notification as close to the failure as possible."** The
  `cd`-guard already did this; the `rc` fix restores it for the agent-call
  path.

Not applied / not evidenced here:

- **Multi-line argument parsing as the cause of the agent failure.** In the
  note that was the visible bug; in our log the agent's failure is clearly the
  keychain login ("Not logged in"), not prompt parsing. The stdin switch is
  still the right hardening, but it was the latent trap here, not the active
  bug.
- **The exit-code caveat ("exit 0 is not proof of work").** Our exit code was
  honestly 1, so it didn't mislead — but the spirit is adopted: notifications
  now carry duration, and verification checks the real outcome (the dated
  `.md` file and the Telegram message), not just the exit code.
- **The Telegram/`security` specifics** are untouched: `notify.sh` was already
  correct by the README's account and is outside what this snapshot can test.
