# Why nightly-review never reported anything

## Causes

1. **The failure reporter was downstream of the failure, and zsh killed it.**
   `bin/nightly-review.zsh` ran `status=$?` on line 19. In zsh, `status` is a
   read-only alias for `$?`, so the assignment aborts the script:

   ```
   /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
   ```

   The script exited before `notify.sh` was reached, so the failure message
   was never sent. I reproduced this locally with a stub `claude` that exits 1:
   the script died on that line and the notifier was never called.

2. **Every run failed because the CLI could not find its login.**
   `nightly-review.err` has six identical pairs, one per run, and
   `launchctl-print.txt` shows `runs = 6`:

   ```
   Not logged in · Please run /login
   /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
   ```

   The job fired on schedule every time. The `last exit code = 1` came from the
   `status` error, not from `claude`. The plist's `EnvironmentVariables` sets only
   `PATH`, with no `USER`. My reading is that a headless `claude` launched by
   launchd then cannot reach its keychain login. I could not confirm this here,
   because the only real test is a launchd run on your machine (see below).

3. **The notifier had never run under launchd, so it was an unverified silent
   path.** `notify.sh` reads the token from the keychain and calls `curl` without
   `-f`, so an HTTP error (bad token, etc.) exits 0 and its body is discarded. If
   the keychain item is missing or locked, the token is empty and the call fails
   silently. I could not confirm this from the logs, since the script never reached
   the notifier. I hardened it anyway.

Causes 1 and 2 are the two layers. Cause 1 hid cause 2.

## Changes

- `bin/nightly-review.zsh`
  - `status=$?` → `rc=$?`.
  - `< /dev/null` on the `claude` call.
  - Failure if `rc != 0` **or** the output is empty (exit 0 with nothing done is
    also a failure).
  - Logs `exit`, `seconds`, and `bytes` for each run to stdout, which goes to
    `nightly-review.out`. The duration is included in the success message.
- `Library/LaunchAgents/com.vk.nightly-review.plist`
  - Added `USER` (`vk`, taken from the paths in this plist) and `HOME`
    (`/Users/vk`) to `EnvironmentVariables`.
- `bin/notify.sh`
  - Exits 1 with a message if the bot token is empty.
  - `curl -fsS` so HTTP errors fail the script.

## What from the colleague's note applied

- **Applied, exactly the same bug:** `status` is read-only in zsh, and the
  assignment sat between the agent call and the failure notification.
- **Applied, matches the log:** "Not logged in" under launchd is fixed by setting
  `USER` in the plist. I also set `HOME`, which the script uses; that is my addition.
- **Applied as hardening:** `< /dev/null` on a prompt passed as an argument. This
  is not the cause here.
- **Applied:** the failure reporter now sits right after the call, with the exit
  code checked. Run duration is logged.
- **Applied:** `runs` and `last exit code` prove the job fired, not that it worked.
  The check is whether the output exists and is fresh.
- **Did not apply:** the "Input must be provided either through stdin or as a
  prompt argument" error. It does not appear in these logs. The prompt was already
  passed as an argument, and the real error was the login.

## How I verified (locally only)

- `zsh -n` on the script passes, and `plutil -lint` passes on the plist.
- Stubbed `claude` runs, with the notifier replaced by a stub that logs its message:
  - claude exits 1: `FAILED`, script exits 1.
  - claude exits 0 with output: `done`, script exits 0.
  - claude exits 0 with empty output: `FAILED`, script exits 1.
- `notify.sh` with no token and a failing `security` stub: exits 1 before any
  network call.
- I did **not** run anything against Telegram or the real `claude` login, did not
  copy files into `~/bin` or `~/Library/LaunchAgents`, and did not load or kick the
  job. The stub tests do not prove that `claude` works under launchd.

## What you need to do

1. Copy the changed files into place and make the script executable:
   ```
   cp bin/nightly-review.zsh bin/notify.sh ~/bin/ && chmod +x ~/bin/nightly-review.zsh ~/bin/notify.sh
   cp Library/LaunchAgents/com.vk.nightly-review.plist ~/Library/LaunchAgents/
   ```
   If your account name is not `vk`, change the `USER` and `HOME` values in the
   plist first.
2. Reload the job:
   ```
   launchctl bootout gui/$UID/com.vk.nightly-review   # may say "not loaded"; ignore
   launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
   ```
3. Run it now and check the real outcome:
   ```
   launchctl kickstart -k gui/$UID/com.vk.nightly-review
   launchctl print gui/$UID/com.vk.nightly-review | grep -E 'runs|last exit'
   tail -n 3 ~/Library/Logs/nightly-review.out      # expect "claude exit=0 seconds=N bytes=M", N not ~0
   ls -l ~/Library/Logs/nightly-review-$(date +%F).md   # expect a fresh summary
   ```
   Expect `last exit code = 0`, a non-trivial duration, a non-empty summary, and
   the Telegram "done" message.
4. Force one failure to test the failure path. For example, temporarily add
   `exit 1` at the top of `~/bin/nightly-review.zsh` (or move `~/projects/shop`
   aside), kickstart again, and confirm the Telegram "FAILED" message arrives.
   Revert the change afterwards.
5. Check `~/Library/Logs/nightly-review.err` for runs after 2026-10-18. The snapshot
   stops there, so later runs are not in these files.
