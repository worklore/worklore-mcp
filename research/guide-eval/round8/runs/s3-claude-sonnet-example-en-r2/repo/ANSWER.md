# Why nightly-review was silent

The job was running the whole time. `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`. The schedule and plist loading were fine. The `.err` log had the answer.

## Causes (two stacked)
1. **Job fails: "Not logged in · Please run /login".** Under launchd the `claude` CLI could not reach its login in the keychain. The plist's `EnvironmentVariables` has no `USER`. Fix: added `USER=vk` to the plist.
2. **The failure reporter dies before reporting.** `nightly-review.zsh:19: read-only variable: status`. `status` is read-only in zsh, so `status=$?` kills the script between the agent call and the `notify.sh` failure call. No notification is ever sent, so everything is silent. Fix: use `rc=$?`.

## Hardening also applied
- `claude -p ... < /dev/null`, because the prompt is an argument and a closed stdin stops the CLI waiting on stdin.
- The run duration is logged to stderr and included in the notification.
- An empty output file now triggers a failure notice, so exit 0 with nothing done can't pass silently.

## Colleague's note: what applied
- Applied: `launchctl print` first (runs, exit code); read the err log; the `status` read-only bug and `rc=$?`; `USER` in the plist; `< /dev/null`; logging duration; checking the real outcome, not just the exit code.
- Not applied: piping the prompt via stdin. Here the prompt arrives fine as an argument, and the error was "Not logged in", not a missing prompt. I used `< /dev/null` instead, as the note's alternative suggests.
- Also noted: the README says 02:30, while the colleague's job ran at 16:50. The plist and the print output both say 02:30, so that is consistent here.

## Not verified
I could not run launchd, `claude` or Telegram here. After copying the files to your home dir, run:
`launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist; launchctl kickstart -k gui/$UID/com.vk.nightly-review`
Then confirm exit code 0, a fresh non-empty output file, a plausible duration and a Telegram message. Force one failure to test the failure path too. If "Not logged in" persists, run `claude /login` once in a normal terminal. `notify.sh` reads the keychain too, so check that it works under launchd.
