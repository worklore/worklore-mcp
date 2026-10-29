# Why the nightly job was silent

Evidence: `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`. The job fired every night; it failed and could not report it. (The log files exist and are not empty: `.err` has the causes.)

## Causes
1. **`claude -p` was "Not logged in"** under launchd. The plist's environment had only `PATH`, no `USER` (and `HOME`), so the CLI could not reach its keychain login. Every run died at once.
2. **`status=$?` in the zsh script** (line 19): `status` is read-only in zsh, so the script aborted ("read-only variable: status") right before the failure notification. The reporter sat downstream of the failure, hence total silence.

## Fixes
- `bin/nightly-review.zsh`: `rc=$?` instead of `status=$?`; `< /dev/null` on the claude call; also treat empty output as failure; log exit code and duration to stderr; exit non-zero on failure.
- plist: added `USER` and `HOME` to `EnvironmentVariables`. Reload it (`launchctl bootout` / `bootstrap gui/$UID ...`) after copying to `~/Library/LaunchAgents`.

## Colleague's note: what applied
- Applied: check `launchctl print` first (runs/exit code); read the stderr log; never assign `status` in zsh; add `USER` to the plist; `< /dev/null` for an argument prompt; log duration; verify real outcome, not just exit code.
- Not applied: "prompt not received, pipe via stdin" — here the prompt is an argument and the actual error was "Not logged in"; I kept the argument form with closed stdin. Also their schedule (16:50) differs; this job runs at 02:30.

## Not verified
I can't run launchd, claude or Telegram here. Please run `launchctl kickstart -k gui/$UID/com.vk.nightly-review`, confirm exit 0, a fresh non-empty output file, a plausible duration, and the Telegram message; then force a failure once to confirm the failure note arrives. If "Not logged in" persists, the keychain may be locked/unavailable to a background session, or `notify.sh`'s `security find-generic-password` may need the same check.
