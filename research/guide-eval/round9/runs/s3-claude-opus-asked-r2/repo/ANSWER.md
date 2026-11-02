# Why nightly-review never reported anything

The job was running the whole time. `launchctl-print.txt` shows `runs = 6`,
`last exit code = 1`, and `Library/Logs/nightly-review.err` has one pair of
lines per night. Three bugs stacked on top of each other:

1. **`claude -p` fails under launchd with "Not logged in · Please run /login".**
   The launchd environment only had `PATH`. There was no `USER`, and at 02:30
   the login keychain can be locked, so the CLI couldn't read its stored login.
   Its stdin was also left open while the prompt was passed as an argument. The
   review therefore failed within a few seconds every night.

2. **`status=$?` killed the script before it could report that failure.**
   In zsh, `status` is a read-only special variable (it's the same as `$?`).
   Assigning to it is a fatal error: `nightly-review.zsh:19: read-only variable:
   status`, exit 1. That line comes right after the `claude` call and before
   the `"$NOTIFY" "nightly review FAILED …"` call, so the failure note never ran.
   This is why there were no messages at all, not even failures.

3. **`notify.sh` would have failed silently too.** Under launchd
   `TG_BOT_TOKEN` isn't set (you only set it by hand when testing). The fallback
   `security find-generic-password` fails when the keychain is locked, and with
   `set -e` the script exits before `curl` runs. The token in
   `.config/nightly-review/config.toml`, which exists for exactly this case, was
   never read. `curl -sS` without `--fail` also treated Telegram HTTP errors as
   success.

## Fixes made

- `bin/nightly-review.zsh`: `rc=$?` instead of `status=$?`. The prompt goes in
  on stdin (`print -r -- "$PROMPT" | claude -p …`). Claude's stderr is kept next
  to the output and its tail is included in the failure message. Each run's exit
  code and duration are logged. A run that exits 0 but writes an empty file now
  counts as a failure. If `~/.config/nightly-review/claude-token` exists, it is
  exported as `CLAUDE_CODE_OAUTH_TOKEN`.
- `bin/notify.sh`: the token is looked up in env, then keychain, then
  `config.toml` (`chat_id` also comes from there). The script prints a clear
  stderr message and exits non-zero if there is no token or the send fails
  (`--fail-with-body`).
- `com.vk.nightly-review.plist`: adds `USER`/`HOME` to `EnvironmentVariables`
  and sets `StandardInPath` to `/dev/null`.

## What you need to do (on the real machine)

1. If the keychain is locked at 02:30, run `claude setup-token` once and save
   the token: `umask 077; pbpaste > ~/.config/nightly-review/claude-token`.
   Also check that the token in `config.toml` is the current bot token.
2. Reload: `launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap
   gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`.
3. Test: `launchctl kickstart -k gui/$UID/com.vk.nightly-review`. You should get
   a Telegram message, a fresh `nightly-review-<date>.md`, a plausible duration
   in the `.err` log, and `last exit code = 0`. Then break it once on purpose
   (for example, point `REPO` at a missing directory) and check that the failure
   note arrives.

## Security note
`README.md` contains a Telegram bot token in plain text, in the `notify.sh`
example. It is also different from the one in `config.toml`. Rotate it with
@BotFather and remove it from the README. `config.toml` and the new
`claude-token` should be `chmod 600`.

None of this was tested against launchd or Telegram (no external calls were
made). Only plist lint, shell syntax checks and an offline run of `notify.sh`
were done.
