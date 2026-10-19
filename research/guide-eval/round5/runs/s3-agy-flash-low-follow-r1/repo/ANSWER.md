# Causes of Silent Launchd Failure

Investigation of the job (`com.vk.nightly-review`), `Library/Logs/nightly-review.err`, and `launchctl-print.txt` revealed three stacked issues that caused the job to fail and remain completely silent:

1. **Missing `USER` in launchd `EnvironmentVariables`**
   - **Symptom:** `Library/Logs/nightly-review.err` showed `Not logged in · Please run /login`.
   - **Cause:** macOS `launchd` executes user agents with a minimal environment that does not include the `USER` environment variable by default. Without `USER`, CLI tools (such as Claude CLI or security tooling accessing the macOS keychain) cannot locate user credentials or keychain entries and fail immediately.
   - **Fix:** Added `USER` (`vk`) to `EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`.

2. **Assignment to Read-Only Variable `status` in zsh**
   - **Symptom:** `Library/Logs/nightly-review.err` showed `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`.
   - **Cause:** In zsh, `status` is a built-in read-only alias for `$?`. Attempting to assign `status=$?` causes zsh to immediately terminate execution with a fatal error. Because this assignment occurred directly between the agent invocation and the error handling / notification command (`"$NOTIFY" ...`), the failure reporter was killed before sending any Telegram alert.
   - **Fix:** Changed `status=$?` and subsequent references to `rc=$?` in `bin/nightly-review.zsh`.

3. **Multi-line Prompt Argument Handling under Scheduled Agent Context**
   - **Symptom / Risk:** Multi-line string arguments passed via `claude -p "$PROMPT"` under launchd can fail or hang awaiting input.
   - **Fix:** Piped the prompt directly via standard input using `print -r -- "$PROMPT" | claude -p ...` in `bin/nightly-review.zsh`.
