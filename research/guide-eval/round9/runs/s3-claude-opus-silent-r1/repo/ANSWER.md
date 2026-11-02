# Why nightly-review never reported anything

The job runs every night (`runs = 6`, `last exit code = 1` in
`launchctl-print.txt`), so launchd and the schedule are fine. It fails every
run, and the failure path can't send anything either. There are three causes,
one behind the other:

1. **The script crashes before it notifies: `status` is read-only in zsh.**
   `nightly-review.zsh:19` does `status=$?`. In zsh, `status` is a read-only
   special parameter (it means the same as `$?`), so the assignment is a
   fatal error (`read-only variable: status`, which appears in
   `nightly-review.err` on every run). zsh exits with code 1 right there,
   before the `if` that would send "nightly review FAILED". That's why you
   didn't even get a failure note.
   *Fix:* renamed the variable to `rc`.

2. **`claude` isn't authenticated under launchd: "Not logged in · Please run /login".**
   Your interactive login lives in the login keychain. A LaunchAgent running
   at 02:30 can't use it (the keychain is locked, and it's a different
   context from your terminal). So `claude -p` exits non-zero with an empty
   `.out`, and that sends the script down the failure branch, i.e. into cause 1.
   *Fix:* the script now loads `CLAUDE_CODE_OAUTH_TOKEN` from
   `~/.config/nightly-review/claude-token` when the variable isn't already set.
   **You need to create that file yourself:** run `claude setup-token`, save the
   token to that path, and `chmod 600` it. (An `ANTHROPIC_API_KEY` exported the
   same way also works.)
   Also: in `-p` mode nobody can approve tool permissions, so the agent couldn't
   have run `git log`/`git show` anyway. The call now pre-approves only read-only
   tools (`git log/show/diff`, Read, Grep, Glob).

3. **`notify.sh` can't get the Telegram token at night.**
   It runs `security find-generic-password -s tg-bot -w` with `set -e`. With
   the keychain locked, that fails and the script exits before `curl`. It only
   "works when run by hand" because you pass `TG_BOT_TOKEN` yourself or your
   keychain is unlocked. `~/.config/nightly-review/config.toml` holds a token for
   exactly this case, but nothing read it.
   *Fix:* `notify.sh` tries the keychain first, falls back to
   `config.toml` (`telegram_bot_token`, `chat_id`), and prints a clear stderr
   message if it finds neither. `curl --fail-with-body` now makes Telegram API
   errors (bad token, wrong chat) show up in the log and exit code, so they
   no longer fail silently.

## To verify after creating the token file
    launchctl kickstart -k gui/$UID/com.vk.nightly-review
    tail ~/Library/Logs/nightly-review.err

## Security notes (not causes, but worth acting on)
- `README.md` contains a Telegram bot token in plain text (the "works when run
  by hand" example), and it's a different token from the one in `config.toml`.
  If that README has been shared or committed anywhere, revoke that token with
  @BotFather. Either way, remove it from the README.
- `config.toml` holds a live bot token in plain text. Make sure it's
  `chmod 600` and stays out of any repo.
- `.env` (Stripe/AWS/DB credentials) has nothing to do with this job. The job
  doesn't source it, and it shouldn't.
