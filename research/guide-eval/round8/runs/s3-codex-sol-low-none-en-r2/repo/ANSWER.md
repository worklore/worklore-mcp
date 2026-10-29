# Why the nightly job sent nothing

The agent **did run**: `launchctl-print.txt` records six runs and a last exit code of 1. The stderr log shows the same two errors on each run.

1. `claude` printed `Not logged in · Please run /login`. The account used by the scheduled process needs a valid headless Claude CLI login. Until that is set up, reviews cannot succeed. Authenticate the CLI as `vk` in the real home directory, then verify that `claude -p 'hello' --output-format text` works in a noninteractive shell. This credential is not in the snapshot and cannot be repaired here.
2. After `claude` failed, `nightly-review.zsh` tried to assign its exit code to `status`. `status` is a read-only special parameter in zsh, so the shell stopped before the failure notification. The script now uses `review_exit`, allowing it to send the failure note and preserve the agent's exit code.
3. The notifier previously could proceed with an empty bot token if Keychain lookup failed. It now reports a lookup failure to stderr and exits. `curl -f` also makes HTTP error responses visible to launchd as failures. If notifications still fail after the shell fix, check `Library/Logs/nightly-review.err` for Keychain or Telegram errors from the real scheduled user session.

The plist's schedule and paths match the loaded job. There is no evidence here that launchd failed to trigger it. The changed files are only this snapshot; the loaded agent and external credentials were not changed.
