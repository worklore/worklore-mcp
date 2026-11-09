# Why the nightly job was silent

The job was never broken — it ran on schedule every night. The evidence was
sitting in the snapshot the whole time:

- `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`.
- `Library/Logs/nightly-review.err` has exactly two lines per run (12 lines =
  6 runs), and nothing was ever written to `nightly-review.out`.

Each run failed in two stacked ways:

## Cause 1 — the agent call fails under launchd: "Not logged in"

Every run's first stderr line is `Not logged in · Please run /login`. The
plist's `EnvironmentVariables` sets `PATH` but not `USER`, so the headless CLI
can't locate its keychain login when launchd spawns it (interactively it
inherits `USER` from your shell, which is why it works by hand). The agent
exits 1 immediately, without reviewing anything.

**Fix:** added `USER=vk` to `EnvironmentVariables` in
`Library/LaunchAgents/com.vk.nightly-review.plist`.

## Cause 2 — `status=$?` kills the script before it can report the failure

`bin/nightly-review.zsh` captured the agent's exit code with `status=$?`.
In zsh, `status` is a read-only special variable (a mirror of `$?`), and
assigning to it is a fatal error: the script aborts on the spot with exit 1.
That line sat between the agent call and the failure-notification branch, so
every night the sequence was: agent fails → messenger dies before speaking →
perfect silence. The second stderr line per run,
`nightly-review.zsh:19: read-only variable: status`, is this bug, and the exit
code 1 in `launchctl print` comes from it.

**Fixes in `bin/nightly-review.zsh`:**

- `status` renamed to `rc` (the failure notification is now reachable; verified
  that a failing agent run produces the FAILED Telegram message).
- The prompt is now piped to the agent via stdin
  (`print -r -- "$PROMPT" | claude -p --output-format text`) instead of being
  passed as a multi-line argument — more robust inside a scheduled shell, and
  it means stdin is a pipe that reaches EOF rather than a tty the CLI could
  block on.
- Each run now logs `exit=<code> duration=<seconds>` to stdout (i.e. into
  `nightly-review.out` under launchd), so you can tell a real review from a
  2-second crash-without-work.

## Which parts of the colleague's note applied

Applied, and they were exactly right:

- **Check reality before theorizing** — `launchctl print` (`runs = 6`,
  `last exit code = 1`) plus the stderr log showed the job fired and failed;
  "launchd isn't running it" was never the problem.
- **The `status` read-only trap in zsh** — Cause 2, verbatim, including the
  messenger being downstream of the failure. Fix `rc=$?` applied.
- **`USER` in the plist's `EnvironmentVariables`** — Cause 1, verbatim: the
  "Not logged in" death from the Mihai Perdum article applied directly.
- **Pass the prompt via stdin rather than as a multi-line argument** —
  applied as a hardening measure.
- **Log each run's duration** — applied (to `nightly-review.out`).
- **The caveat that an exit code only proves the script ran, not that it
  worked** — true here too: the failure notification never fired despite a
  well-defined exit code, so the real outcome (Telegram message, fresh review
  file) is what matters; the duration line helps detect "exit 0 but did
  nothing".

Not applied / not applicable:

- **`< /dev/null` with a prompt-as-argument** — unnecessary once the prompt is
  piped via stdin (the pipe delivers EOF on its own); kept the pipe approach
  instead.
- **Exit-0-on-timeout watchdog caveat** — no watchdog in this job, though the
  new duration line guards against the equivalent "green but empty" case.
- The note's reproduction steps involving a live `launchctl kickstart` — this
  snapshot isn't the live machine, so verification was done with a stubbed
  `claude` and a stubbed notifier (no external calls), exercising the exact
  script and plist from the snapshot.

## Verification done here (stubbed harness, since this is a snapshot)

- Original script + failing agent stub → exit 1, **no** notification —
  reproduces your symptom exactly.
- Fixed script + failing agent stub → exit 1, FAILED notification sent.
- Fixed script + succeeding agent stub → exit 0, success notification with the
  review summary, fresh `nightly-review-<date>.md` written, duration logged.
- `plutil -lint` on the edited plist: OK.

## What to do on the real machine

1. Copy the two changed files into place (`bin/nightly-review.zsh`,
   `Library/LaunchAgents/com.vk.nightly-review.plist`), then reload:
   `launchctl bootout gui/$UID/com.vk.nightly-review` and
   `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`.
2. `launchctl kickstart -k gui/$UID/com.vk.nightly-review`, then confirm all of:
   `last exit code = 0`, a fresh `nightly-review-<date>.md` exists with real
   content, the run took a plausible amount of time (not a few seconds), and
   you got the Telegram summary.
3. Break it on purpose once (e.g. temporarily point `REPO` at a missing path)
   and confirm you get the failure message too. After that, silence in either
   direction should be impossible.
