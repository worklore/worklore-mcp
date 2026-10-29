# Why nightly-review never reports anything

Two causes stack. Together they hide each other.

1. **`claude` is not logged in when launchd runs it.** `Library/Logs/nightly-review.err` shows
   `Not logged in · Please run /login` on every run (6 runs). The job's `claude -p` exits non-zero
   under launchd, which has no access to your interactive login session.
   **Not fixed here, because it needs your credentials.** Run `claude setup-token` once and put the
   token in the job as `CLAUDE_CODE_OAUTH_TOKEN` (or `ANTHROPIC_API_KEY`). Either add it to the
   plist's `EnvironmentVariables`, or have the script read it from the Keychain.
   Keep it out of the repo. Then reload the agent with `launchctl bootout` and `launchctl bootstrap`.

2. **The failure handler crashed, so no failure note was ever sent.** The script used
   `status=$?`, but in zsh `status` is a read-only special variable (an alias of `$?`).
   The err log shows `nightly-review.zsh:19: read-only variable: status`. The script died on
   that line, before reaching the `notify.sh "... FAILED ..."` call.
   **Fixed:** the variable is now `rc` in `bin/nightly-review.zsh`.

With the fix alone you will start getting "nightly review FAILED (exit 1)" Telegram notes each
night, until cause 1 is resolved.

## Things I checked and left alone
- The plist and the schedule (02:30) are fine. `launchctl print` shows 6 runs, so launchd does fire the job.
- `notify.sh` reads the bot token from the login Keychain (`security find-generic-password`).
  I could not test it here. If the Keychain is locked, or the item's ACL doesn't allow `security`
  in the launchd context, the failure note may still not arrive. If so, set `TG_BOT_TOKEN` in the
  job environment.
