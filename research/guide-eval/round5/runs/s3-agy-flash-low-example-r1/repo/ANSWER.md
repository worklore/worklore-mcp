# Causes of Nightly Job Failure and Fixes

## 1. Causes Found

From inspecting `launchctl-print.txt` and `Library/Logs/nightly-review.err`:
- `launchctl print gui/501/com.vk.nightly-review` showed that the job had fired (`runs = 6`), but exited with `last exit code = 1`.
- `nightly-review.err` contained repeating pairs of errors:
  1. `Not logged in · Please run /login`
  2. `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`

Specifically, two distinct issues caused the job to fail and stay completely silent:

1. **Missing `USER` environment variable in launchd (`com.vk.nightly-review.plist`)**:
   Under macOS `launchd`, user agents run with a minimal environment that omits `USER` unless explicitly provided. Without `USER`, CLI tools such as `claude` (and `security` / macOS keychain integration) fail to resolve user credentials from the keychain and exit with `Not logged in · Please run /login`.

2. **Assigning to read-only variable `status` in `zsh` (`bin/nightly-review.zsh`)**:
   In `zsh`, `status` is a special read-only built-in variable aliased to `$?`. Attempting to assign `status=$?` causes `zsh` to terminate the script immediately with a fatal error (`read-only variable: status`). Because this assignment was placed right after the `claude` command and before the `"$NOTIFY"` call, the failure notifier was killed before it could send any notification to Telegram.

3. **Multi-line argument vs stdin for headless CLI**:
   Passing multi-line prompt strings as direct CLI arguments under scheduled shell wrappers can run into argument parsing/quoting or stdin-hanging issues with headless CLI tools. Piping the prompt cleanly via standard input (`print -r -- "$PROMPT" | claude -p ...`) prevents prompt handling failures.

---

## 2. Colleagues Note: Which Parts Applied

### What Applied:
- **`launchctl print gui/$UID/<job-label>` check**: Applied directly. The job was running (`runs = 6`), but failing (`last exit code = 1`), confirming launchd was firing and the failure was within the job execution.
- **`status` is read-only in zsh**: Applied directly. Line 19 of `bin/nightly-review.zsh` executed `status=$?`, immediately fatal-erroring and preventing the downstream failure notification from running. Changing this to `rc=$?` resolved the silence.
- **Missing `USER` in `EnvironmentVariables`**: Applied directly. The headless CLI died with `Not logged in · Please run /login` because `USER` was not defined in the plist's `EnvironmentVariables`. Setting `USER=vk` enables keychain login resolution under launchd.
- **Piping prompt via stdin**: Applied as a robust fix to ensure reliable prompt delivery to headless agent calls under launchd (`print -r -- "$PROMPT" | claude -p ...`).

### What Did Not Apply:
- **The specific failure message `"Input must be provided either through stdin or as a prompt argument"`**: In the colleague's case, the prompt argument failed to reach the agent call. In this setup, the immediate cause of the agent failure was `Not logged in · Please run /login`.
- **Closed stdin (`< /dev/null`) when prompt is an argument**: Since we pipe the prompt via stdin (`print -r -- "$PROMPT" | claude -p ...`), standard input is already provided with the prompt data and EOF rather than needing `< /dev/null`.

---

## 3. Changes Made

1. **Updated [Library/LaunchAgents/com.vk.nightly-review.plist](file:///tmp/h-UIPY38/Library/LaunchAgents/com.vk.nightly-review.plist)**:
   - Added `<key>USER</key><string>vk</string>` to `EnvironmentVariables`.

2. **Updated [bin/nightly-review.zsh](file:///tmp/h-UIPY38/bin/nightly-review.zsh)**:
   - Changed prompt passing to pipe via stdin: `print -r -- "$PROMPT" | claude -p --output-format text > "$OUT"`.
   - Replaced `status=$?` with `rc=$?` and updated references to use `$rc`.
