# Why the nightly job was silent

The job **did run**. The captured `launchctl print` shows six runs, a calendar
trigger at 02:30, and `last exit code = 1`. Its stderr repeats the same two
errors on each run:

1. `claude -p` reported `Not logged in · Please run /login`. The agent cannot
   produce a review until Claude is authenticated for this unattended job.
   The `.env` in this snapshot contains shop deploy credentials, not a Claude
   credential. A launchd job running `/bin/zsh script` also does not read
   `~/.zshrc`, so the interactive shell setup cannot be relied on here.
2. After Claude failed, `nightly-review.zsh` assigned its exit code to
   `status`. In zsh, `status` is read-only. That assignment terminated the
   script before its failure notification.
3. Even if that assignment had succeeded, `notify.sh` looked up the Telegram
   token in the keychain. The snapshot says that keychain is locked at 02:30;
   the token in `.config/nightly-review/config.toml` was never read. The
   notifier would have failed too.

## Local fixes

- The wrapper now captures Claude's exit code in `exit_code` and sends a
  failure message that points to the stderr log. Successful reviews still
  send the summary.
- The notifier reads the Telegram token and chat ID from the existing local
  TOML config, with environment overrides for manual use. It no longer
  depends on the nightly keychain state. `curl -f` also makes HTTP failures
  visible to launchd's stderr log.
- The README's example no longer contains a literal bot token.

The snapshot has no usable Claude authentication to install. Authenticate
Claude for unattended use on the actual Mac before expecting review summaries.
Until then, the corrected job should send a failure note rather than fail
silently. The edited files have **not** been installed or reloaded on that Mac.

## Verification

`zsh -n`, `bash -n`, and `plutil -lint` passed. An isolated local run with
stubbed `claude` and `curl` confirmed both paths: a Claude exit code of 7
produced a failure notification and remained exit code 7; a successful review
produced a summary notification and exited 0. No external service was called.
