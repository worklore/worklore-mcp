# Causes of Silent Nightly Review Failures

The launchd job (`com.vk.nightly-review`) has actually been firing on schedule every night (`runs = 6`, `last exit code = 1` in `launchctl-print.txt`), but two stacked bugs (plus a latent launchd stdin/argument trap) caused the review to fail and prevented the failure notification from ever being sent:

## 1. Missing `USER` in `EnvironmentVariables` (`Not logged in · Please run /login`)
- **Where:** `Library/LaunchAgents/com.vk.nightly-review.plist`
- **Why it failed:** Under `launchd`, only `PATH` and `XPC_SERVICE_NAME` were present in the job's environment (`launchctl-print.txt`). Without `USER` set in `EnvironmentVariables`, the headless `claude` CLI cannot locate its authentication credentials in the macOS Keychain and immediately exits with `Not logged in · Please run /login` (recorded in `Library/Logs/nightly-review.err`).
- **Fix:** Added `<key>USER</key><string>vk</string>` (and `<key>HOME</key><string>/Users/vk</string>`) to `EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`.

## 2. Assigning to read-only variable `status` in `zsh` (`read-only variable: status`)
- **Where:** `bin/nightly-review.zsh` (line 19)
- **Why it silenced failure reporting:** Immediately after `claude -p ...` failed, the script attempted to capture the exit code with `status=$?`. In `zsh`, `status` is a read-only built-in special parameter (an alias for `$?`). Assigning to `status` caused `zsh` to abort execution immediately with `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`, before reaching the `if [ ... -ne 0 ]` block that calls `bin/notify.sh`.
- **Fix:** Replaced `status` with a non-reserved variable name (`rc=$?`).

## 3. Unclosed stdin / multi-line prompt argument with `claude -p` under `launchd`
- **Where:** `bin/nightly-review.zsh` (line 18)
- **Why it is a trap:** Running `claude -p "$PROMPT"` under `launchd` without piping stdin or redirecting `< /dev/null` can cause `claude -p` to hang waiting on stdin or fail to parse multi-line prompt arguments in a non-interactive scheduled shell. Additionally, checking only the exit code does not guard against empty output (`[ ! -s "$OUT" ]`).
- **Fix:** Piped the prompt into `claude -p` via stdin (`print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"`) and verified that `$OUT` is non-empty before reporting success.
