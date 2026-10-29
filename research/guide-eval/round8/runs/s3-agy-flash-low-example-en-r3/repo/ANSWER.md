# Root Causes of Silent Failure

The nightly launchd job was failing silently due to two primary causes:

1. **`claude` CLI authentication failure (`USER` missing in `launchd` environment)**:
   In `Library/LaunchAgents/com.vk.nightly-review.plist`, only `PATH` was specified under `EnvironmentVariables`. Launchd jobs run in a minimal environment that does not export `USER` by default. Without `USER`, `claude` cannot locate or access login credentials in the macOS keychain, immediately exiting with `Not logged in · Please run /login` (as seen in `Library/Logs/nightly-review.err`).

2. **Assignment to zsh read-only variable `status` killing the failure messenger**:
   In `bin/nightly-review.zsh` line 19, the script executed `status=$?`. In `zsh`, `status` is a special built-in read-only variable (an alias for `$?`). Assigning to `status` is a fatal error in zsh (`read-only variable: status`), immediately terminating the script before it could reach the error check and invoke `bin/notify.sh` to report the failure.

Additionally, under launchd when passing a prompt via command line arguments (`claude -p "$PROMPT"`), headless CLIs can hang or behave unpredictably waiting on stdin if stdin is not closed. Adding `< /dev/null` ensures stdin is properly closed.

---

# Fixes Applied

1. **`Library/LaunchAgents/com.vk.nightly-review.plist`**:
   - Added `<key>USER</key><string>vk</string>` under `EnvironmentVariables` so the `claude` CLI can access the user's keychain login.

2. **`bin/nightly-review.zsh`**:
   - Replaced assignment to the read-only variable `status=$?` with `rc=$?` (and updated downstream references to `$rc`).
   - Added `< /dev/null` to the `claude -p` invocation to prevent stdin blocking in unattended launchd executions.

---

# Colleague Note: Which Parts Applied

- **Applied**:
  - **`status` is read-only in zsh**: Directly matched `Library/Logs/nightly-review.err` line `/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`. This assignment sat directly between the agent invocation and `bin/notify.sh`, killing the script before the failure notification could be sent.
  - **Setting `USER` under `EnvironmentVariables` in the plist**: Directly addressed the root failure cause `Not logged in · Please run /login`. Under launchd, `USER` was unset, preventing keychain credential discovery.
  - **Closing stdin (`< /dev/null`) when prompt is an argument**: Applied as recommended practice for unattended launchd agent execution to prevent waiting on stdin.
  - **Checking `launchctl print` and `StandardErrorPath` logs**: The snapshot's `launchctl-print.txt` and `Library/Logs/nightly-review.err` accurately confirmed the job was running (exit code 1) and showed both errors.

- **Did Not Apply**:
  - **Piping prompt via stdin (`print -r -- "$PROMPT" | claude -p ...`)**: The colleague's error was `"Input must be provided either through stdin or as a prompt argument"` due to prompt argument passing issues. In this case, `claude -p "$PROMPT"` was accepted, but failed due to missing `USER`/keychain login.
