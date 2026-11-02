# Root Causes of Silent Launchd Failures

The nightly launchd job (`com.vk.nightly-review`) was failing silently without reporting any status or failure notifications due to two distinct issues:

1. **Claude CLI failed to authenticate (`USER` environment variable missing in launchd context)**:
   - **Symptom**: In `Library/Logs/nightly-review.err`, the job logged `Not logged in · Please run /login` on every scheduled execution.
   - **Cause**: Jobs executed via macOS `launchd` run in a minimal environment that does not export `USER` by default (as seen in `launchctl-print.txt` under `environment`). Without `USER`, CLI tools such as Claude Code cannot locate or access the user's keychain credentials / session tokens, leading to an immediate exit code 1.
   - **Fix**: Added `USER` with value `vk` to `<key>EnvironmentVariables</key>` in `Library/LaunchAgents/com.vk.nightly-review.plist`.

2. **Zsh fatal error when assigning to `status` killed the notification handler**:
   - **Symptom**: In `Library/Logs/nightly-review.err`, `nightly-review.zsh:19: read-only variable: status` occurred immediately following the Claude CLI failure.
   - **Cause**: In Zsh, `status` is a special read-only variable aliased to `$?`. Attempting to assign `status=$?` terminates the script execution immediately before the error handling block `if [ $status -ne 0 ]; then "$NOTIFY" ... fi` can ever be reached. Thus, the failure notification via `notify.sh` was never executed.
   - **Fix**: Replaced variable assignment `status=$?` with `rc=$?` and updated references to `$rc` in `bin/nightly-review.zsh`. Additionally added `< /dev/null` to the headless `claude` invocation to prevent waiting on stdin under non-interactive launchd execution.
