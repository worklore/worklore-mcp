# Why the nightly review was silent

The agent **did run**. `launchctl-print.txt` records six runs and a last exit code of 1. The empty stdout log is therefore not evidence of a missed schedule. The stderr log records the same two errors on every run.

1. `claude -p` reported `Not logged in · Please run /login`. The scheduled process did not have a usable headless CLI login. I added explicit `USER=vk` and `HOME=/Users/vk` to the launchd environment so the CLI can look up that user's login. This cannot establish or verify a login from the snapshot; the installed CLI still needs a valid login on the Mac.
2. Immediately after the agent call, the zsh script assigned `status=$?`. `status` is a read-only special parameter in zsh. That assignment terminated the script before its failure notification, explaining why the CLI error never reached Telegram. The script now uses `rc` and sends a failure note for a nonzero exit or empty output.
3. The notifier ignored `.config/nightly-review/config.toml`. With no `TG_BOT_TOKEN` in launchd's environment, it would try the keychain, which the snapshot says is locked at night. The notifier now reads the configured token and chat ID, while still allowing a supplied token or keychain fallback. It also treats HTTP errors from Telegram as failures.

The review now closes the CLI's stdin so an unattended invocation cannot wait for input. The token was also present in the README example and the config file was readable by other local users; I removed the example value and restricted the config and `.env` files to owner access.

The plist change needs to be loaded on the actual Mac before it affects the scheduled job. No live launchd job or external service was touched here. Verification in this snapshot used mocked `claude`, `curl`, and `security`: CLI failure sent a failure note and exited 42; empty output sent a failure note and exited 1; a successful review sent a summary and exited 0. A real end-to-end run still depends on the Mac's CLI login and Telegram delivery.
