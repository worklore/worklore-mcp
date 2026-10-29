# Why nightly-review was silent

Evidence: `launchctl-print.txt` shows `runs = 6`, `last exit code = 1` — the job fires on schedule (02:30) and fails; it is not a launchd scheduling problem. `Library/Logs/nightly-review.err` shows two stacked errors, repeated every run.

## Causes
1. **`claude -p` fails with "Not logged in"** under launchd. The launchd environment has no `USER` (only PATH/XPC_SERVICE_NAME), so the CLI can't find its login in the keychain. Fix: added `USER` to `EnvironmentVariables` in the plist.
2. **`status=$?` in the zsh script** (line 19): `status` is a read-only special variable in zsh, so the script aborts right there ("read-only variable: status"), before the failure `notify.sh` call. The failure reporter never ran, hence total silence. Fix: use `rc=$?`.

## Other hardening (in `bin/nightly-review.zsh`)
- `< /dev/null` on the `claude -p` call so it never waits on stdin.
- Logs rc and duration to stderr each run.
- Also treats an empty output file as failure (exit 0 with no work done).

## Colleague's note: what applied
- Applied: `launchctl print` first (runs/last exit code); read the err log; the zsh `status` bug; `USER` in the plist; `< /dev/null`; log duration; check real outcome, not just exit code.
- Not applied: piping the prompt via stdin (the prompt is a single-argument string and the actual error was "Not logged in", not a missing prompt); the 16:50 schedule (ours is 02:30).

## To do on your machine (not done here)
Reload the plist (`launchctl bootout` / `bootstrap gui/$UID ...`), copy the files into `~`, make sure `claude` is logged in in the GUI session, then `launchctl kickstart -k gui/$UID/com.vk.nightly-review` and confirm last exit code 0, a fresh non-empty output file, a plausible duration, and the Telegram message. Force one failure to test the failure path. Note `notify.sh` reads the keychain too; if it fails under launchd, its error will now land in the .err log only — verify that it delivers when kicked off by launchd. I could not run any of this here.
