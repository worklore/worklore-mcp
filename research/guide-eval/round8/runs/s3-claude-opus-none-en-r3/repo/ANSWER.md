# Why the nightly review never reported anything

launchd *is* running the job. `launchctl print` shows `runs = 6` and
`last exit code = 1`, and `nightly-review.err` has one pair of lines per night.
Each night, two bugs happened in a row:

## 1. `claude` is not authenticated under launchd (the job's real failure)

`nightly-review.err`: `Not logged in · Please run /login`

launchd starts `/bin/zsh script.zsh` without a login shell, so `~/.zshrc` and
`~/.zprofile` are never read. Only the plist's `PATH` is set. Whatever
`claude` uses when you run it by hand (for example an `ANTHROPIC_API_KEY` or
token exported in your shell profile, or a credential the 02:30 launchd
context can't reach) is not there. So `claude -p` exits 1 right away. Stdout
was redirected to the dated `.md` file, which explains why
`nightly-review.out` is empty.

## 2. `status=$?` kills the script before it can send the failure note

`nightly-review.err`: `nightly-review.zsh:19: read-only variable: status`

In zsh, `status` is a read-only special parameter (an alias of `$?`). Assigning
to it is a fatal error in a non-interactive script. The script aborted on
line 19 with exit 1, so neither the failure branch nor the success branch, and
so neither `notify.sh` call, ever ran. That's why you got no failure note
either. (The script works in bash, where `status` is an ordinary variable.
Reproduced with `zsh -c 'true; status=$?; echo after'`, which never prints
"after".)

## Fixes made

`bin/nightly-review.zsh`
- Renamed `status` to `rc`.
- Sources `~/.config/nightly-review.env` if it exists, so the job gets its
  secrets without relying on shell rc files.
- `claude`'s stderr goes to `$OUT.err`. The failure notification now includes
  the last part of that error, so you'd have received "Not logged in" on
  Telegram.
- Timestamped log lines go to the launchd `.err` log. A failing `notify.sh` is
  logged instead of failing silently.
- Headless `-p` mode can't ask for permission, so read-only tools
  (`Read`, `Grep`, `Glob`, `git log/show/diff`) are pre-approved with
  `--allowedTools`. Otherwise, after auth is fixed, the agent would be refused
  the `git log` it needs.
- The prompt now puts the 3-line summary first, and the message sends up to
  3500 chars. The old `head -c 300` sent the *start* of the output, but the
  summary was asked for at the *end*.

`bin/notify.sh`
- `curl --fail-with-body`, with output going to stderr. Before, a Telegram API
  error (bad token, wrong chat id) still exited 0 and the reply went to
  `/dev/null`.

## What you need to do once (needs your machine)

1. Create a long-lived token and put it in the env file:
   ```sh
   claude setup-token            # prints a token
   mkdir -p ~/.config
   printf 'export CLAUDE_CODE_OAUTH_TOKEN=%s\n' '<token>' > ~/.config/nightly-review.env
   chmod 600 ~/.config/nightly-review.env
   ```
   (Or `export ANTHROPIC_API_KEY=...` if you use an API key.) If the Telegram
   keychain lookup ever fails under launchd, add `export TG_BOT_TOKEN=...`
   there too.
2. Test it the way launchd runs it, rather than from your terminal:
   `launchctl kickstart -k gui/$UID/com.vk.nightly-review`, then check
   `~/Library/Logs/nightly-review.err` and Telegram.

The plist itself is fine and doesn't need to be reloaded. The changes are in
the scripts it calls.
