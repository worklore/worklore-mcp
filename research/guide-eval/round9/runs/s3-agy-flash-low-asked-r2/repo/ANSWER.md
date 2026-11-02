# Root Causes for Why the Nightly launchd Job Never Reported Anything

Investigation of `launchctl-print.txt`, `Library/Logs/nightly-review.err`, `bin/nightly-review.zsh`, `bin/notify.sh`, and `Library/LaunchAgents/com.vk.nightly-review.plist` revealed that the launchd job was indeed firing every night on schedule (6 runs recorded, exit code 1), but suffered from stacked failures that created complete silence:

### 1. Missing `USER` Environment Variable in LaunchAgent plist
* **What happened:** In `com.vk.nightly-review.plist`, only `PATH` was defined under `EnvironmentVariables`. `launchd` runs jobs in an empty/minimal environment without standard user shell variables such as `USER`.
* **Impact:** Headless `claude` relies on `USER` to locate its keychain credentials/session. Without `USER`, `claude` aborted immediately with:
  ```
  Not logged in · Please run /login
  ```
* **Fix:** Added `<key>USER</key><string>vk</string>` to `EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`.

---

### 2. Assignment to Read-Only Variable `status` in Zsh
* **What happened:** In `bin/nightly-review.zsh`, line 19 executed:
  ```zsh
  status=$?
  ```
* **Impact:** In `zsh`, `status` is a built-in special variable (an alias for `$?`) and is strictly read-only. Assigning to `status` caused `zsh` to terminate the script immediately with a fatal error:
  ```
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
  Because this fatal error occurred directly after `claude` exited and right before the failure-handling logic (`if [ $status -ne 0 ]; then "$NOTIFY" ...`), the failure notification call to `notify.sh` was never reached.
* **Fix:** Replaced `status` with `rc` (`rc=$?` and `$rc`) in `bin/nightly-review.zsh`.

---

### 3. Keychain Access Failure in `notify.sh` During Unattended Nightly Runs
* **What happened:** `bin/notify.sh` attempted to resolve `TG_BOT_TOKEN` via:
  ```bash
  : "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
  ```
  At 02:30 when the job runs unattended, the macOS login keychain is typically locked (or unavailable to launchd non-interactive sessions without credentials). A fallback configuration file (`~/.config/nightly-review/config.toml`) had been provided specifically for this scenario, but `notify.sh` was not reading it. If `notify.sh` had been invoked without an unlocked keychain, the `security` command would fail or prompt interactively, preventing Telegram notifications.
* **Fix:** Updated `bin/notify.sh` to check for and load `telegram_bot_token` (and `chat_id`) from `~/.config/nightly-review/config.toml` before attempting the keychain lookup, and prevented `security` failure from aborting under `set -e`.

---

### 4. Unattended Stdin Handling for Headless Agent
* **What happened:** When running `claude -p "$PROMPT"` under a non-interactive launchd context without redirecting stdin, headless CLI tools can stall waiting for terminal stdin.
* **Fix:** Added `< /dev/null` to the `claude` invocation in `bin/nightly-review.zsh`.
