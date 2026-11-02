# Why the nightly launchd job never reported anything

The job *does* run. `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`,
and `Library/Logs/nightly-review.err` has one pair of lines per night. Three bugs
stack up so that every run fails and nothing gets reported:

1. **`claude -p` fails with "Not logged in · Please run /login".** Under launchd
   the CLI doesn't get your login session. The plist sets only `PATH`, so
   `USER` is missing and the CLI can't find its credentials in the keychain. On
   top of that, the login keychain may be locked at 02:30. Because the prompt is
   passed as an argument, stdin was also left open, which can hang `claude -p`
   under launchd.
2. **`status=$?` kills the script (`nightly-review.zsh:19: read-only variable: status`).**
   In zsh, `status` is a read-only special parameter (it's the same as `$?`).
   Assigning to it aborts the script on the line between the failed `claude`
   call and the failure notification. So the failure note was never sent. This
   is the reason there was *total* silence instead of a failure message.
3. **`notify.sh` would have failed too.** It gets the bot token with
   `security find-generic-password`. At night the keychain is locked, so that
   call fails, and with `set -e` the script exits before `curl` runs. It never
   read `~/.config/nightly-review/config.toml`, the file that exists for exactly
   this case. (Testing it by hand works because you pass `TG_BOT_TOKEN` in the
   environment and your keychain is unlocked.)

## Fixes made

- `bin/nightly-review.zsh`: use `rc=$?` instead of `status`. Run `claude` with
  `< /dev/null` and write its stderr to `$OUT.err`. Treat a non-zero exit *or*
  an empty output file as a failure, and put the start of the error in the
  failure message.
- `bin/notify.sh`: try the keychain first. If that fails, read
  `telegram_bot_token` from `config.toml`. If there is still no token, print a
  clear error to stderr and exit.
- `com.vk.nightly-review.plist`: add `USER=vk` to `EnvironmentVariables` and add
  `~/.local/bin` to `PATH`, which is where the native `claude` installer puts the
  binary.
- `config.toml`: set to `chmod 600` because it holds a bot token.

Checks run: `zsh -n`, `bash -n` and `plutil -lint` pass. With stubbed `claude`,
`security` and `curl`, the failure path now sends
"nightly review FAILED (exit 1): Not logged in". `notify.sh` falls back to the
config token when the keychain call fails.

## What you still need to do (I didn't touch your live system)

- Reload the agent:
  `launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`
  Then test it with `launchctl kickstart -k gui/$UID/com.vk.nightly-review`.
  Check that you get a Telegram message and a fresh, non-empty
  `nightly-review-YYYY-MM-DD.md`.
- If you still get "Not logged in" because the keychain is locked at 02:30, run
  `claude setup-token`. Store the token in a file only you can read
  (`chmod 600`), then `export CLAUDE_CODE_OAUTH_TOKEN` from it in the script.
  Don't put it in the plist.
- Security: `README.md` contains a Telegram bot token in plain text, and it is
  not git-ignored. Remove it and revoke it with @BotFather. Do **not** source
  `~/.env` (Stripe/AWS/DB secrets) in this job. The agent doesn't need them.
