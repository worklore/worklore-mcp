# Why the nightly job was silent

Evidence: `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`, so the job fires on schedule. The `.err` log shows two stacked failures, repeated every run.

1. **`claude -p` fails with "Not logged in"** under launchd. The plist's environment has no `USER`, so the CLI can't find its login in the keychain. The agent exits non-zero and does no work.
2. **`status=$?` kills the script** (`read-only variable: status`, zsh). This sits between the agent call and the failure notification, so the failure reporter dies before sending anything. That is why nothing ever arrived on Telegram.

## Fixes
- `bin/nightly-review.zsh`: `status` -> `rc`; `< /dev/null` on the agent call; run duration logged to stderr; an empty output file now counts as failure (exit 0 isn't proof of work); the notify wrapper logs to stderr if Telegram delivery itself fails.
- `Library/LaunchAgents/com.vk.nightly-review.plist`: added `USER=vk` under `EnvironmentVariables`.

After copying these to your home dir, reload the job (`launchctl bootout` then `bootstrap gui/$UID ...`; the plist is only read at load). Then run `launchctl kickstart -k gui/$UID/com.vk.nightly-review`. Check the exit code, a fresh non-empty `nightly-review-<date>.md`, a plausible duration, and the Telegram message. Then force a failure once to test the failure path. I could not run any of this here (no launchd, claude or Telegram in the sandbox). Only `zsh -n` syntax was checked.

## Colleague's note: what applied
- Applied: `launchctl print` first (the runs and exit code were already in your capture); read the stderr log; `status` read-only in zsh; `USER` in the plist; `< /dev/null`; duration logging; the exit-0-isn't-success caveat.
- Not applied: the "prompt not received, pipe via stdin" bug. Your log shows no such error, and your prompt is passed as an argument with stdin closed, which the note says is fine.
- Not applicable: the note's 16:50 schedule. Yours is 02:30, and I left it alone. README says 02:30, and the plist agrees.
- Unverified: `notify.sh` reads its token from the keychain. It works by hand but may need the login keychain unlocked when run unattended. If failure notes still don't arrive, check the "notify failed" line in the `.err` log.
