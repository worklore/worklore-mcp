# Root Causes for Nightly Job Failures and Fixes

There were two independent root causes preventing the nightly launchd job from reporting anything (including failures) to Telegram:

## 1. Syntax Error in `bin/nightly-review.zsh`: Assigning to Read-Only Variable `status`
- **Cause**: In `zsh`, `status` is a built-in special variable that mirrors `$?` and is marked read-only. In `bin/nightly-review.zsh`, line 19 attempted to assign `status=$?`. When executed under `zsh`, this failed immediately with the fatal error:
  ```text
  /Users/vk/bin/nightly-review.zsh:19: read-only variable: status
  ```
  Because the script aborted immediately at line 19, execution never reached lines 21–24 (`"$NOTIFY" "nightly review FAILED..."`).
- **Fix**: Renamed `status` to `exit_code` (e.g. `exit_code=$?` and checked `[ $exit_code -ne 0 ]`).

---

## 2. Keychain Access Failure in `bin/notify.sh` During Non-Interactive / Nightly Runs
- **Cause**: In `bin/notify.sh`, the Telegram bot token was resolved via:
  ```bash
  : "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"
  ```
  When running non-interactively at night (02:30) via launchd, macOS Keychain is typically locked or cannot be accessed non-interactively without prompt permissions, causing `security find-generic-password` to return an error code. Under `set -eu`, this aborted the notification script immediately before `curl` could be executed.
  
  While the fallback configuration file `.config/nightly-review/config.toml` existed with the token and chat ID specifically for when the keychain is locked, `bin/notify.sh` never checked or read this file.
- **Fix**: Updated `bin/notify.sh` to check for and read `telegram_bot_token` and `chat_id` from `${HOME}/.config/nightly-review/config.toml` when `TG_BOT_TOKEN` is not already provided in the environment, only falling back to macOS Keychain (`security`) if not found.

---

*(Note: In addition, `claude` reported `Not logged in · Please run /login` during the runs because the launchd environment lacked credentials/login state or keychain access to the auth session, which will now properly trigger and report the failure notification via Telegram).*
