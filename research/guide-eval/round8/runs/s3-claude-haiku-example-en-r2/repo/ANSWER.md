# Why nightly-review never reported anything

## Short answer

The job ran every night. It failed, and the failure reporter was dead before it
could speak. Two causes stacked:

1. **Root cause: `claude` could not log in under launchd.** Every run logged
   `Not logged in · Please run /login`. The plist sets only `PATH` in
   `EnvironmentVariables`, and the `launchctl print` output shows no `USER` in the
   job's environment. Without `USER`, the CLI cannot find its login in the keychain.
2. **Why it was silent: `status=$?` killed the script.** In zsh, `status` is a
   read-only variable. Assigning to it aborts the script with
   `read-only variable: status`. That line sat between the agent call and the
   Telegram failure notification, so the job failed and the notifier never ran.

## Evidence

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`. launchd fired the job on
  schedule, every night. "Launchd is not firing" was never the problem.
- `Library/Logs/nightly-review.err`: 6 entries, one per run. Each run shows
  `Not logged in` followed by `nightly-review.zsh:19: read-only variable: status`.
  Line 19 is the `status=$?` line.
- `Library/Logs/nightly-review.out`: empty. The job never printed anything, so it
  had no run-duration or progress log.
- I reproduced the original script with a stubbed `claude` that exits 1: it
  printed the read-only error and sent no notification.

## What applied from the colleague's note

- **Applied: read-only `status`.** Same error in the log. Fixed by renaming to `rc`.
- **Applied: `USER` must be set in the plist.** The `Not logged in` error matches
  the note, and `USER` is absent from the job environment. Added
  `<key>USER</key><string>vk</string>`. I have not confirmed this live, because I
  cannot run launchd for your user from this snapshot. It is the most likely fix,
  and the next run will show whether it worked.
- **Applied as a hardening step: closed stdin.** The prompt is an argument, so I
  added `< /dev/null` to `claude`. The log shows no sign that this step was
  hanging, so this is defensive, not a confirmed cause.
- **Applied: a green exit code with nothing done.** The script now treats an empty
  output file as a failure, even if `claude` exits 0.
- **Applied: log each run's duration.** The script now writes start, exit, and
  duration lines to stdout, which lands in `nightly-review.out`.
- **Did not apply: the stdin prompt bug** (`print -r -- "$PROMPT" | claude -p`).
  The log has no `Input must be provided either through stdin or as a prompt
  argument` error, so the prompt was reaching `claude`. I did not change how the
  prompt is passed.
- **Already true: the failure notification is on the failure path.** It sits
  right after the `rc` check. The problem was only the variable name.

## What changed

- `bin/nightly-review.zsh`
  - `status=$?` → `rc=$?` (fixes the silent death).
  - `< /dev/null` on the `claude` call.
  - Failure if `rc` is non-zero **or** the output file is empty.
  - Start, exit-code, and duration lines in the log.
- `Library/LaunchAgents/com.vk.nightly-review.plist`
  - Added `USER` = `vk` to `EnvironmentVariables`. The username comes from the
    `/Users/vk` paths in this snapshot. Run `id -un` and change it if it differs.

## Verification done here

- `zsh -n` passes on the script. `plutil -lint` passes on the plist.
- Ran the fixed script in a throwaway HOME with a stubbed `claude`:
  - `claude` exits 1 → Telegram-failure stub called, exit 1.
  - `claude` exits 0 with output → success stub called with the summary, exit 0.
  - `claude` exits 0 with no output → failure stub called, exit 1.
- Not verified: launchd itself, the real keychain login, and real Telegram delivery.
  Those need the steps below on your machine.

## To deploy and verify (on your Mac; I did not touch `~/`)

```sh
cp bin/nightly-review.zsh ~/bin/nightly-review.zsh
cp Library/LaunchAgents/com.vk.nightly-review.plist ~/Library/LaunchAgents/
launchctl bootout gui/501 ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl bootstrap gui/501 ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/501/com.vk.nightly-review
launchctl print gui/501/com.vk.nightly-review | grep -E 'runs|last exit|USER'
```

Then check all three:

- `last exit code = 0`.
- `~/Library/Logs/nightly-review-<today>.md` exists and is fresh.
- The run took a plausible time (tens of seconds or more), not a second or two.
  The duration line is in `~/Library/Logs/nightly-review.out`.
- You received the "done" message on Telegram.

To check the failure path, temporarily move `~/projects/shop` aside, run
`launchctl kickstart -k` again, and confirm the "repo missing" message arrives.
Move the repo back afterward.

If `last exit code` is still 1 after this, read `nightly-review.err` first. If the
run succeeds but Telegram stays silent, suspect `notify.sh`: its keychain lookup
(`security find-generic-password -s tg-bot -w`) may fail under launchd. Its errors
go to the same `.err` log.

## Takeaway

When automation is silent, first check whether it ran (`launchctl print`: runs and
last exit code). Then read the stderr log. Then check whether the failure reporter
sits downstream of the failure. Here it did. Also, a run that finishes in seconds
with no output did no work, even if its exit code is 0.
