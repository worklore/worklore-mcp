# Why the nightly review never reported anything

The job does run. `launchctl print` shows `runs = 6` and `last exit code = 1`,
and `nightly-review.err` has one pair of lines for each run:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

There are two separate bugs, and together they make it silent.

## 1. The failure path crashes: `status` is read-only in zsh (this is why you got nothing at all)

In zsh, `status` is a built-in special parameter (an alias for `$?`) and
can't be assigned to. Line 19 (`status=$?`) is a fatal error in a
non-interactive zsh script. The script stops right there with exit 1, before
it reaches either `"$NOTIFY"` call. So even when `claude` failed, the failure
note was never sent. (You can reproduce it with `zsh -c 'status=1'`.)

**Fix:** rename the variable to `rc`.

## 2. `claude` is not authenticated when launchd runs it (this is why every run fails)

launchd starts the script with a bare environment: only the PATH from the
plist, plus HOME and similar. Nothing from your interactive shell is there,
because a non-interactive `/bin/zsh script` does not read `~/.zshrc` or
`~/.zprofile`. Whatever logs `claude` in for you in Terminal is not available
to the job, so `claude -p` prints "Not logged in" and exits non-zero. That
could be an exported `ANTHROPIC_API_KEY`/token, or an interactive `/login`
session that headless use under launchd doesn't pick up.

**Fix:** give the job its own credential. Run `claude setup-token` once (it
creates a long-lived token for headless use) and store the token in the login
keychain:

```
security add-generic-password -U -a "$USER" -s claude-oauth-token -w
```

The script now reads it into `CLAUDE_CODE_OAUTH_TOKEN` at startup, the same
way `notify.sh` reads the Telegram token. If the token is missing, the script
sends a failure note instead of dying quietly. Keeping the token in the
keychain also keeps it out of the plist.

## Smaller problems fixed in the same edit

- **No useful error in the failure note.** `claude`'s stderr went to the
  shared `.err` file, and the note only pointed to an empty `.md`. Stderr now
  goes to a dated `nightly-review-YYYY-MM-DD.err`, and its first 300 chars are
  included in the Telegram message.
- **The review couldn't read the commits.** In `-p` mode nothing can approve
  tool use, so `git log`/`git show` would have been denied. Read-only tools
  are now pre-approved with `--allowedTools` (git log/show/diff, Read, Grep,
  Glob). Nothing that writes files is allowed, which also enforces
  "Do not modify any file".

## What you still need to do (on the real machine)

1. `claude setup-token`, then store the token with the `security` command above.
2. Copy the new `bin/nightly-review.zsh` into `~/bin/`. The plist doesn't
   change, so you don't need to reload it.
3. Test it the way launchd runs it: `launchctl kickstart gui/$UID/com.vk.nightly-review`,
   then check Telegram and `~/Library/Logs/nightly-review-*.err`.
