# Why the nightly job never reported anything

Every run (6 so far) failed the same way, and the failure path was broken too,
so nothing was ever sent.

1. **`claude` is not logged in in the launchd context.** `Library/Logs/nightly-review.err`
   shows `Not logged in · Please run /login` on every run. The job's `claude -p`
   exits non-zero, so there is never a summary. Not fixable from this folder:
   run `claude setup-token` in a terminal and put the resulting token in the
   plist's `EnvironmentVariables` as `CLAUDE_CODE_OAUTH_TOKEN` (or an
   `ANTHROPIC_API_KEY`), then reload the agent. I did not add a token.

2. **The failure notice could never be sent: `status` is read-only in zsh.**
   `status=$?` in `bin/nightly-review.zsh` gives
   `read-only variable: status` (also in the err log). zsh's `$status` is a
   special alias of `$?`, so the assignment fails, the script exits with 1
   and `notify.sh` is never reached. This is why even failures were silent.
   Fixed: the variable is now `rc`.

3. (Hardening) `notify.sh` used `curl -sS` without `--fail`, so Telegram HTTP
   errors (bad token, wrong chat id) would be swallowed silently. Added `--fail`
   so the error shows up in the err log.

After setting the token, test with:
`launchctl kickstart gui/$UID/com.vk.nightly-review` and check Telegram and
`~/Library/Logs/nightly-review.err`.
