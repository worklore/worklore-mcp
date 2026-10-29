# Why the nightly review never reported anything

Short version: the job dies on line 19 of `nightly-review.zsh` before it ever
calls `notify.sh`, so neither a summary nor a failure note is sent. Behind
that, `claude -p` also cannot log in when launchd runs it. The notifier also
fails silently, so even a correct failure note could be lost.

## Causes

### 1. `status` is a read-only variable in zsh (the job aborts before notifying)

`bin/nightly-review.zsh` does `status=$?`. In zsh, `status` is a special
read-only parameter (a synonym for `$?`), so the assignment is a fatal error:

    /Users/vk/bin/nightly-review.zsh:19: read-only variable: status

The script exits there, so the `notify.sh` calls on lines 22 and 26 never run.
That is why there is no summary and no failure message, even though the job
ran. Evidence:

- `Library/Logs/nightly-review.err` has this error six times.
- `launchctl-print.txt` shows `runs = 6` and `last exit code = 1`.
- I reproduced it with zsh 5.9: `status=$?` exits with status 1 and never
  reaches the next line.

Fix: renamed the variable to `claude_rc`, and the script now always notifies
on failure.

### 2. `claude -p` is not logged in under launchd

`Library/Logs/nightly-review.err` also shows, from the same runs:

    Not logged in · Please run /login

The job runs `claude` from launchd, and launchd does not see the interactive
login. Even with cause 1 fixed, every run would have failed here. Claude Code
on this machine reads `CLAUDE_CODE_OAUTH_TOKEN` (the binary contains that
name), so the fixed script takes a long-lived token from the keychain item
`claude-nightly-oauth`. I did not create that token: `claude setup-token` is
interactive and needs your subscription. See "What you need to do" below.

### 3. `notify.sh` can fail silently (affects every message, including failure notes)

`bin/notify.sh` had two problems:

- `: "${TG_BOT_TOKEN:=$(security find-generic-password -s tg-bot -w)}"`
  does not trigger `set -e` when the keychain lookup fails. The token ends up
  empty, and curl posts to `https://api.telegram.org/bot/sendMessage`.
  I reproduced this with a stub `security` that fails: the script reached the
  curl call with an empty token.
- `curl -sS` exits 0 on an HTTP error from Telegram (bad token, bad chat), and
  its output went to `/dev/null`. A rejected message looked like success.

The keychain lookup may also behave differently under launchd than in a
terminal. The notifier "works when run by hand", but I could not test it
from launchd, so this one is unconfirmed on your machine.

Fix: the token lookup now fails loudly to stderr (which launchd records in
`nightly-review.err`), and curl uses `-f`, so Telegram HTTP errors are
reported.

## What changed

- `bin/nightly-review.zsh`
  - `status` renamed to `claude_rc`, so the script no longer aborts.
  - Auth comes from `CLAUDE_CODE_OAUTH_TOKEN`, read from the keychain item
    `claude-nightly-oauth`. If it is missing, the job sends a failure note and exits 1.
  - claude's stderr goes to `~/Library/Logs/nightly-review-<date>.err`
    instead of only the launchd log, and the first 200 bytes of it are quoted
    in the failure note.
  - A zero exit with empty output counts as a failure.
- `bin/notify.sh`
  - Missing token: prints an error and exits 1 instead of posting an empty token.
  - `curl -fsS`: Telegram rejections exit non-zero.
- The plist is unchanged. The scripts are read fresh on each run, so copying
  them into `~/bin` is enough; no `launchctl` reload is needed.

## Verification

I ran the original and fixed scripts in a sandbox with stub `claude`,
`security`, and `curl`, so nothing reached Telegram or Anthropic:

| Case | Original | Fixed |
|---|---|---|
| claude succeeds | aborts at line 19, no notify | sends "done" with the summary |
| claude "Not logged in", exit 1 | aborts at line 19, no notify | sends "FAILED (exit 1): Not logged in …" |
| claude exit 0, empty output | (not reached) | sends "FAILED … no output from claude" |
| no `claude-nightly-oauth` token | (not reached) | sends "FAILED: no claude-nightly-oauth token" |
| no `tg-bot` token (notify alone) | posts to `/bot/sendMessage` | prints error, exit 1, no curl call |
| Telegram returns HTTP error | exit 0, silent | exit 22 (non-zero) |

Both scripts pass `zsh -n` / `bash -n`. I did not run the job against the
real `~/projects/shop`, claude, or Telegram.

## What you need to do

1. Create the Claude token in a terminal:
   `claude setup-token`
2. Store it in the keychain for the job:
   `security add-generic-password -s claude-nightly-oauth -a "$USER" -w`
   (paste the token at the prompt)
3. Copy `bin/nightly-review.zsh` and `bin/notify.sh` into `~/bin/`.
4. Test the real path once:
   `launchctl kickstart -k gui/501/com.vk.nightly-review`
   This sends a real Telegram message. Either a summary or a `FAILED` note
   should arrive. If neither does, check `~/Library/Logs/nightly-review.err`.
   If the failure is in the keychain lookup of `tg-bot` (cause 3), that log
   will say so.
