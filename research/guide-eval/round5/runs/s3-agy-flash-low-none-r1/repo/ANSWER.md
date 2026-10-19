# Causes of Failure and Fixes

## 1. Primary Cause: Read-only variable assignment in zsh (`status=$?`)
- **Location:** `bin/nightly-review.zsh`, line 19
- **Error in logs (`Library/Logs/nightly-review.err`):**
  ```
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
- **Explanation:** In `zsh`, `status` is a special built-in variable that aliases `$?` and is marked read-only. Attempting to assign `status=$?` causes a fatal runtime error in `zsh`, terminating script execution immediately before it can check the exit status or call `bin/notify.sh` with the failure notice.
- **Fix:** Changed the variable name from `status` to `exit_code`:
  ```zsh
  exit_code=$?

  if [ $exit_code -ne 0 ]; then
    "$NOTIFY" "nightly review FAILED (exit $exit_code), see $OUT"
    exit $exit_code
  fi
  ```

---

## 2. Underlying Claude Failure: Missing `USER` environment variable in launchd
- **Error in logs (`Library/Logs/nightly-review.err`):**
  ```
  Not logged in · Please run /login
  ```
- **Explanation:** 
  1. `launchd` executes jobs in a minimal environment that does not populate standard session environment variables like `USER` (or `LOGNAME`).
  2. Claude Code looks up credentials in the macOS Keychain under the service name `Claude Code-credentials` with the account matching `process.env.USER`.
  3. When `process.env.USER` is missing (and `os.userInfo().username` fallback cannot resolve or falls back to `"claude-code-user"`), Claude Code queries Keychain for account `"claude-code-user"` instead of the actual user account name.
  4. The keychain lookup fails to find matching credentials, prompting Claude to report `Not logged in · Please run /login` and exit with status 1.
- **Fix / Recommendation for launchd environment:**
  Ensure the launchd job or script provides `USER` (and `HOME`) in the environment. In `Library/LaunchAgents/com.vk.nightly-review.plist`, add `USER` to `<key>EnvironmentVariables</key>` (or export `USER="$(id -un)"` in the script wrapper):
  ```xml
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>USER</key>
    <string>vk</string>
  </dict>
  ```
