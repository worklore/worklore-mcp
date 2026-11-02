# Why the nightly job was silent

The agent was scheduled and did run. `launchctl-print.txt` records six runs and a last exit code of 1. The stderr log shows the same two errors on each run.

1. `claude` exited with `Not logged in · Please run /login`. This prevents a review summary. The snapshot contains no usable unattended Claude authentication, so successful summaries still require setting that up for the launchd user.
2. Immediately afterward, `nightly-review.zsh` assigned `$?` to `status`. In zsh, `status` is a read-only special parameter. That assignment aborted the script before its failure-notification branch. The script now uses `review_exit_code`, so a Claude failure reaches the notifier and retains its exit code.
3. `notify.sh` ignored the token and chat ID in `.config/nightly-review/config.toml`. When launched without `TG_BOT_TOKEN`, it tried the login keychain, which the README says is locked at 02:30. It now reads the existing config, with environment variables taking precedence and the keychain only as a token fallback.
4. The notifier previously discarded the Telegram response without making HTTP errors fail the command. It now uses `curl --fail --show-error` and a timeout, so delivery errors appear in launchd stderr and return a failure status.

The launchd plist already supplies a usable command path; `~/.zshrc` and its `.env` are not loaded by this noninteractive job. Neither explains the recorded zsh error. The Telegram token is present in tracked files, including Git history. It should be rotated and stored outside version control; this snapshot was not deployed or sent to any external service.

Local checks used mocked `claude`, `curl`, and `security`: review failure, missing repository, notifier failure, and review success all took their expected paths. No Telegram or other external request was made.
