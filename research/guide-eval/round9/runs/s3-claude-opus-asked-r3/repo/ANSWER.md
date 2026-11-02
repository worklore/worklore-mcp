# Why the nightly review never reported anything

The job *did* run. `launchctl-print.txt` shows `runs = 6`, `last exit code = 1`, and
`Library/Logs/nightly-review.err` has one pair of lines per night. Three bugs stacked
up, and each one hid the one before it.

## Causes

1. **`claude` is not logged in under launchd** (`Not logged in · Please run /login`).
   A launchd agent gets a bare environment. The plist set only `PATH`, so `USER`
   (and, to be safe, `HOME`) were missing, and the CLI couldn't find its login in
   the keychain. The review died within seconds every night.

2. **`status=$?` kills the script, so the failure note never gets sent**
   (`nightly-review.zsh:19: read-only variable: status`). In zsh, `status` is a
   read-only special parameter. Assigning to it aborts the script with exit 1,
   on the line right before the `if` that calls `notify.sh`. The failure reporter
   sat downstream of the failure, which is why you didn't even get failure notes.

3. **`notify.sh` would have failed at 02:30 anyway.** It reads the bot token with
   `security find-generic-password`, and on this box the login keychain is locked
   at night. Under `set -e` that failure exits silently. `~/.config/nightly-review/config.toml`
   was created for exactly this case, but nothing ever read it. (Running it by hand
   works because you pass `TG_BOT_TOKEN` yourself and the keychain is unlocked.)

## Fixes made

- `Library/LaunchAgents/com.vk.nightly-review.plist`: added `USER=vk` and
  `HOME=/Users/vk` to `EnvironmentVariables`, and put `~/.local/bin` (the native
  installer's location for `claude`) on `PATH`.
- `bin/nightly-review.zsh`:
  - `status` → `rc`.
  - The prompt now goes in on stdin (`print -r -- "$PROMPT" | claude -p ...`), so
    `claude` can't hang waiting on an open stdin.
  - Each run's start time, exit code and duration go to the `.err` log.
  - An exit 0 with an empty output file now counts as a failure.
  - If notifying fails, that is written to the log too.
- `bin/notify.sh`: token comes from `$TG_BOT_TOKEN`, then the keychain, then
  `config.toml` (along with `chat_id`). If none of these give a token it writes a
  clear error to the log. `curl -f` makes HTTP errors (e.g. a bad token) fail
  instead of passing as success.
- Made `config.toml` readable by you only (`chmod 600`).

## To do on the real machine (not done here)

```sh
launchctl bootout gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review | grep 'last exit'
tail ~/Library/Logs/nightly-review.err
```

Check that the exit code is 0, that the run took more than a few seconds, that
today's `nightly-review-*.md` exists and has content, and that the Telegram message
arrived. Then force one failure (e.g. temporarily point `REPO` at a missing
directory) and check that the failure note arrives too.

If `claude` still reports "Not logged in" when the keychain is locked, run
`claude setup-token` once. Store the token it gives you in a file only you can
read, and export it as `CLAUDE_CODE_OAUTH_TOKEN` from the script. Don't put it
in the plist.

## Security notes

- `README.md` contains a live-looking Telegram bot token in plain text, and it
  differs from the one in `config.toml`. Remove it from the README and consider
  revoking it with @BotFather.
- I did not touch `.env`.
