# Why the Nightly Launchd Job Never Reported Anything

## Root Causes

Inspection of [`launchctl-print.txt`](file:///tmp/h-9T56Cl/launchctl-print.txt) and [`Library/Logs/nightly-review.err`](file:///tmp/h-9T56Cl/Library/Logs/nightly-review.err) shows that `launchd` **did** run the job on schedule every night (`runs = 6`, `last exit code = 1`), producing 6 identical two-line failures in `nightly-review.err`:

```text
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

Two stacked bugs caused the job to fail and prevented [`bin/notify.sh`](file:///tmp/h-9T56Cl/bin/notify.sh) from ever running, with a third latent trap waiting once authentication succeeded:

1. **Missing `USER` in `EnvironmentVariables` caused `claude` to fail authentication (`Not logged in · Please run /login`)**
   - [`Library/LaunchAgents/com.vk.nightly-review.plist`](file:///tmp/h-9T56Cl/Library/LaunchAgents/com.vk.nightly-review.plist) only set `PATH` under `EnvironmentVariables` (confirmed in `launchctl-print.txt`).
   - Without `USER` set (`vk`), `claude` running under `launchd` could not find its login credentials in the macOS Keychain and exited immediately with code `1`.

2. **Assigning `status=$?` in `zsh` crashed the script before the failure notification (`read-only variable: status`)**
   - In [`bin/nightly-review.zsh`](file:///tmp/h-9T56Cl/bin/nightly-review.zsh) (line 19), the script assigned `status=$?`.
   - In `zsh`, `status` is a read-only built-in special parameter. Assigning to it immediately terminated the script on line 19 before reaching the `if [ $status -ne 0 ]; then "$NOTIFY" ...` block on lines 21–24.

3. **Unclosed `stdin` on `claude -p "$PROMPT"` and no check for empty output**
   - Line 18 invoked `claude -p "$PROMPT" --output-format text > "$OUT"` without closing standard input (`< /dev/null`). Under `launchd`, once `USER` is set and Keychain login succeeds, `claude -p` with a prompt argument can hang waiting on `stdin` if `stdin` is not redirected from `/dev/null` (or piped via `stdin`).
   - Additionally, the script only checked the exit code and did not verify that `$OUT` was non-empty (`[ ! -s "$OUT" ]`).

---

## Fixes Applied

- **[`Library/LaunchAgents/com.vk.nightly-review.plist`](file:///tmp/h-9T56Cl/Library/LaunchAgents/com.vk.nightly-review.plist)**: Added `<key>USER</key><string>vk</string>` under `EnvironmentVariables` so `claude` can access the Keychain login under `launchd`.
- **[`bin/nightly-review.zsh`](file:///tmp/h-9T56Cl/bin/nightly-review.zsh)**:
  - Replaced the read-only `status` variable with `rc` (`rc=$?`).
  - Redirected `stdin` from `/dev/null` (`claude -p "$PROMPT" --output-format text < /dev/null > "$OUT"`) so `claude -p` does not hang waiting on `stdin` under `launchd`.
  - Added run duration logging (`SECONDS=0`) and a non-empty output check (`[ ! -s "$OUT" ]`) so an empty output file is also caught and reported as a failure with a non-zero exit code.

---

## Which Parts of the Colleague's Note Applied (and Which Did Not)

### Applied
- **Checking `launchctl print` and `StandardErrorPath` logs first**: [`launchctl-print.txt`](file:///tmp/h-9T56Cl/launchctl-print.txt) (`runs = 6`, `last exit code = 1`) and [`Library/Logs/nightly-review.err`](file:///tmp/h-9T56Cl/Library/Logs/nightly-review.err) proved `launchd` fired on schedule all 6 nights and revealed the exact error lines.
- **Never assigning to `status` in `zsh` (`status=$?` → `rc=$?`)**: Directly explained why the script died on line 19 (`read-only variable: status`) right before calling `notify.sh`.
- **Setting `USER` in the plist's `EnvironmentVariables` (from the 2026-09-30 Correction)**: Directly explained why `claude` failed with `Not logged in · Please run /login` under `launchd`.
- **Closing `stdin` (`< /dev/null`) when passing the prompt as an argument to `claude -p` (from the 2026-09-30 Correction)**: Applied to `claude -p "$PROMPT"` in `bin/nightly-review.zsh` to prevent `claude` from waiting on `stdin` under `launchd`.
- **Verifying the real outcome (`$OUT` non-empty) and logging run duration (from the 2026-09-30 Correction & Steps)**: Applied to `bin/nightly-review.zsh` so a `0` exit code with an empty output file cannot masquerade as success.

### Did Not Apply / Ignored
- **Colleague's Bug 1 (`"Input must be provided either through stdin or as a prompt argument"` from broken multi-line argument parsing)**: Did not occur here. Because `bin/nightly-review.zsh` already passed `"$PROMPT"` as a quoted variable inside the script, `claude` did not fail on missing prompt input; its actual failure in `nightly-review.err` was `Not logged in · Please run /login`.
- **Watchdog exiting `0` on timeout**: No watchdog wrapper is used in this job.
- **Running live `launchctl kickstart` or sending live Telegram test notifications**: This workspace is an offline snapshot (with `launchctl-print.txt` already captured), and the ground rules prohibit operating outside the current directory or contacting external services.
