# Why the nightly job never reported anything

## Cause 1 — the failure path crashed before it could notify (the direct cause of the silence)

`bin/nightly-review.zsh:19` was:

```zsh
status=$?
```

`status` is a **reserved read-only special variable in zsh** (it mirrors `$?`).
Assigning to it is a fatal error in a non-interactive zsh script, so every run
aborted at line 19 — *before* reaching the `if [ $status -ne 0 ]` block that
calls `notify.sh`. The job ran, claude failed, the script died, no Telegram
message was ever sent: no summaries, no failure notes.

Evidence:

- `Library/Logs/nightly-review.err` pairs claude's error with
  `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status` on every
  one of the 6 runs — and nothing from the script appears after that line.
- `launchctl print` shows `runs = 6`, `last exit code = 1` — six nights, all
  failed the same way.
- Reproduced locally with stubbed `claude`/`notify.sh`: the unmodified script
  exits 1 and `notify.sh` is never invoked.

## Cause 2 — claude itself never worked under launchd

Every run's stderr begins with `Not logged in · Please run /login`: the CLI
found no usable credentials in the launchd context (the login from the
interactive shell doesn't carry over). So even with Cause 1 fixed, the job
would only ever have sent failure notes, not summaries. Cause 1 is exactly why
you never saw those notes and couldn't tell.

This can't be remediated from the snapshot (no credential material here, and
authenticating involves external calls). The fixed script now puts the reason
in the failure message, e.g. `nightly review FAILED (exit 1): Not logged in ·
Please run /login`, so the remaining step is self-announcing each night until
you do it (see "Remaining action" below).

## Cause 3 — latent silencers in the notifier (hardened)

`bin/notify.sh` could also fail without a trace:

- `set -eu` meant a failed `security find-generic-password` or `curl` killed it
  silently. Under launchd the keychain item may also be gated by an ACL that
  covers your terminal but not the launchd job — the same class of problem as
  Cause 2, and the reason "works when run by hand" doesn't transfer.
- `curl` had no `--fail`, so an HTTP error from Telegram looked like success.

## Fixes applied

`bin/nightly-review.zsh`
- Capture claude's exit code in `rc` instead of the read-only `status` — the
  failure branch now runs and notifies.
- Merge claude's stderr into the per-day run log (`> "$OUT" 2>&1`) so the log
  is self-contained and the failure message contains the actual error instead
  of pointing at a file on the Mac.
- If `notify.sh` itself fails, log a trace to stderr (launchd writes it to
  `nightly-review.err`) and exit non-zero so `launchctl print` shows it.

`bin/notify.sh`
- Explicit, loud error if the `tg-bot` keychain item can't be read.
- `curl --fail` and a loud error if the Telegram API request fails.

Not causes: the schedule fired fine (6 runs for 6 nights), PATH was fine
(claude did execute), and the plist's log paths work — the evidence is in them.

## Verification

Harness with stubbed `claude` and notifier, no external calls:
- claude fails → exit 1, notifier receives `nightly review FAILED (exit 1):
  Not logged in · Please run /login` (the message production never sent).
- claude succeeds → exit 0, notifier receives `nightly review done: …`.
- notifier fails → script exits 1 and leaves `nightly-review: notify.sh
  failed` on stderr.
- `notify.sh` with unreadable keychain item → exit 1 with a clear stderr
  message.
- `zsh -n` / `bash -n` pass on both scripts. End-to-end with the real claude
  and Telegram was not run, as the ground rules exclude external calls.

## Remaining action (on the real machine, outside this snapshot)

Make claude's credentials usable by the launchd job — how depends on where the
installed claude stores them (keychain item ACL must allow the launchd context,
or supply a token to the job). Until then you'll at least get a nightly
failure note stating the reason.
