# Why the nightly review never reported anything

The job was never silent because launchd didn't fire — it fired on schedule every
night and failed the same way all six times. Silence came from the failure
reporter dying before it could speak, on top of an underlying failure that was
logged but never read.

## Evidence

- `launchctl print gui/501/com.vk.nightly-review` (captured 2026-10-18): `runs = 6`,
  `last exit code = 1`, `state = waiting` — the job ran every night since being
  loaded on 2026-10-12 and exited non-zero every time.
- `Library/Logs/nightly-review.err` existed the whole time and contains the same
  two lines repeated for every run:
  - `Not logged in · Please run /login` (from `claude`)
  - `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status` (from zsh)
- `nightly-review.out` is empty; no `nightly-review-*.md` output was ever produced.

## Cause 1 — the job fails every night: `USER` is missing from the launchd environment

`Library/LaunchAgents/com.vk.nightly-review.plist` sets only `PATH` in
`EnvironmentVariables`. In the launchd context there is no `USER`, so the headless
`claude` CLI cannot locate its login in the keychain and dies immediately with
`Not logged in · Please run /login`. The error appeared six times in the stderr
log — once per scheduled run — and the run ends within seconds, long before doing
any review work.

Fix: added `USER` = `vk` to `EnvironmentVariables` in the plist.

## Cause 2 — the one that made it all invisible: `status=$?` kills the script

`bin/nightly-review.zsh:19` assigned `status=$?`. In zsh, `status` is a read-only
special variable (an alias for `$?`); assigning to it aborts the script on the
spot. That line sat between the `claude` call and the failure-notification branch,
so on every failed run the script died at line 19 and the
`"nightly review FAILED ..."` message never executed. The job failed, then the
messenger died before speaking — two layers of silence.

Fix: renamed to `rc=$?` throughout the failure branch (use `rc`, never `status`,
in zsh).

## Cause 3 (latent, fixed as prevention) — multi-line prompt as an argument

The prompt was passed as one multi-line `"$PROMPT"` argument to `claude -p`.
The stderr log shows the runs died with `Not logged in` before prompt parsing
ever mattered, so this had not bitten yet — but it is the same trap called out
in the colleague's note, and would have surfaced the night Cause 1 got fixed.

Fix: the prompt is now piped via stdin (`print -r -- "$PROMPT" | claude -p ...`),
which is robust inside a scheduled shell.

## Other hardening applied

- Each run now logs its duration (`$SECONDS`) and includes it in both Telegram
  messages, so a "success" that took two seconds is visible as suspicious.
- Failure notification sits immediately after the `claude` call — as close to the
  top of the failure path as possible, per the note.

`bin/notify.sh` was **not** changed: nothing in the evidence implicates it, it
works when run by hand, and it was never actually reached in the launchd runs.

## Which parts of the colleague's note applied

Applied, and confirmed by the evidence:

- **Check reality before theorizing** — `launchctl print` showed `runs = 6`,
  `last exit code = 1`: the job fired on schedule every night. The debugging
  question was never "did it run" but "why does its failure go unreported".
- **Read the `StandardErrorPath` log before theorizing** — the log existed and
  contained the exact two errors; this case was the note's story replayed almost
  verbatim.
- **Never assign to `status` in zsh — use `rc=$?`** — this was the silencer
  (line 19). Direct hit.
- **Set `USER` under `EnvironmentVariables` in the plist** — this was the
  underlying failure (`Not logged in`). Direct hit.
- **Pass the prompt via stdin rather than as a multi-line argument** — applied
  as prevention (see Cause 3).
- **Log each run's duration** — applied.
- **Put the failure notification near the top of the failure path** — applied.

Not applied / not applicable here:

- **`< /dev/null` when the prompt is an argument** — moot once the prompt goes
  through stdin; the pipe itself gives `claude` a non-tty, immediately-EOF stdin.
- **The exit-code caveat** ("the exit code tells you *that* it ran, not *that it
  worked*") — noted as good practice; here the exit code (1) happened to be
  honest. The duration logging added above is the guard against a green exit 0
  with nothing done.

## Verification performed

- `zsh -n bin/nightly-review.zsh` — syntax OK.
- `plutil -lint` on the plist — OK.
- Ran the real script end-to-end twice in a scratch HOME with a stub `claude`
  (which records its stdin) and a stub `notify.sh` (which records messages):
  - success run: exit 0, summary written to the dated output file, prompt
    confirmed delivered via stdin, "done" notification sent with the summary text.
  - forced-failure run: exit 1, "FAILED (exit 1)" notification sent — the
    messenger now speaks in both directions.

## To deploy on the real Mac

This folder is a snapshot; the fixes live in the snapshot's
`bin/nightly-review.zsh` and `Library/LaunchAgents/com.vk.nightly-review.plist`.
Copy both into place, then reload the job so the plist change takes effect:

```sh
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
```

Then force one run with `launchctl kickstart -k gui/$UID/com.vk.nightly-review`
and confirm: a Telegram message arrives, a fresh `nightly-review-*.md` exists,
and the run took a plausible amount of time. No real Telegram message or `claude`
login was exercised here, per the ground rules — that first live kickstart is the
end-to-end proof.
