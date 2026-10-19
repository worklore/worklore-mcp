launchctl print shows runs = 6, last exit code = 1: the job fires, the script fails. Two causes in the stderr log:
1. `Not logged in`: under launchd the CLI cannot reach its keychain login because USER is not set in the job environment. Added USER to EnvironmentVariables in the plist.
2. `read-only variable: status` on line 19: the script assigns `status=$?`, which zsh forbids, so the script dies before the failure notification. Renamed to `rc`.
