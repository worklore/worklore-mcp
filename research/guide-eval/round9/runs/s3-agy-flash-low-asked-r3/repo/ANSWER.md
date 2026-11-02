# Causes for the Nightly Launchd Job Failure and Silence

The launchd job `com.vk.nightly-review` failed to execute successfully and remained completely silent (reporting neither output nor failure) due to four interconnected causes:

---

### 1. Missing `USER` Environment Variable in Launchd Plist
* **Issue:** Under macOS `launchd`, user agent jobs do not inherit standard interactive login shell environment variables such as `USER` unless explicitly provided.
* **Impact:** Claude Code (`claude -p`) requires the `USER` environment variable to access the user's keychain / authentication credentials. Without `USER`, `claude` failed immediately with:
  ```text
  Not logged in · Please run /login
  ```
  as observed in [Library/Logs/nightly-review.err](file:///Library/Logs/nightly-review.err).
* **Fix:** Added `<key>USER</key><string>vk</string>` under `EnvironmentVariables` in [Library/LaunchAgents/com.vk.nightly-review.plist](file:///Library/LaunchAgents/com.vk.nightly-review.plist).

---

### 2. Assignment to Read-Only Builtin Variable `status` in Zsh
* **Issue:** In `zsh`, `status` is a special read-only variable (an alias for `$?`).
* **Impact:** Line 19 of [bin/nightly-review.zsh](file:///bin/nightly-review.zsh) attempted `status=$?`. When executed in zsh, assigning to a read-only variable immediately aborts script execution:
  ```text
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
  Because this fatal error occurred right after `claude` failed and before the failure notification block (`if [ $status -ne 0 ]; then "$NOTIFY" ...`), the script crashed before it could call [bin/notify.sh](file:///bin/notify.sh).
* **Fix:** Renamed the return code variable from `status` to `rc` in [bin/nightly-review.zsh](file:///bin/nightly-review.zsh).

---

### 3. Passing Multi-line Prompt as an Argument to Headless Agent
* **Issue:** Passing multi-line prompt arguments to `claude -p "$PROMPT"` under a headless/non-interactive `launchd` context can cause input parsing and stdin inheritance issues.
* **Impact:** Scheduled headless agents can fail to receive prompts cleanly or stall/fail unless piped via stdin.
* **Fix:** Updated the invocation in [bin/nightly-review.zsh](file:///bin/nightly-review.zsh) to pipe the prompt via stdin:
  ```zsh
  print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"
  ```

---

### 4. Keychain Locked Unattended at Night & Notifier Missing Config Fallback
* **Issue:** [bin/notify.sh](file:///bin/notify.sh) retrieved the Telegram bot token via `security find-generic-password -s tg-bot -w`. At 02:30, unattended machines frequently have their keychain locked, which causes `security find-generic-password` to fail or hang. While [.config/nightly-review/config.toml](file:///config/nightly-review/config.toml) was created specifically for this machine where the keychain is locked at night, [bin/notify.sh](file:///bin/notify.sh) never read it.
* **Impact:** Even if [bin/notify.sh](file:///bin/notify.sh) had been reached by the failure handler, it would have failed to retrieve `TG_BOT_TOKEN` from the locked keychain and exited with an error under `set -e`.
* **Fix:** Updated [bin/notify.sh](file:///bin/notify.sh) to read `telegram_bot_token` and `chat_id` from `$HOME/.config/nightly-review/config.toml` (falling back to the `security` command if not found).
