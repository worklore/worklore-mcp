# Why the nightly review never reported anything

launchd itself is fine. `launchctl-print.txt` shows `runs = 6` and
`last exit code = 1`, which is one run per night from 10-13 to 10-18, and
`nightly-review.err` has exactly 6 pairs of lines. The job ran every night
and failed in the script every time. Two bugs together made it fail without
sending anything.

## Cause 1: `claude` is not authenticated under launchd (why it fails)

```
Not logged in · Please run /login
```

Your interactive `claude /login` session isn't available to a headless run
started by launchd (on macOS it lives in the login Keychain / your terminal
session). So `claude -p` exits 1 every night before it reviews anything.

**Fix (manual, one time; I did not create any secrets):**

```sh
claude setup-token                     # prints a long-lived token
mkdir -p ~/.config/nightly-review
cat > ~/.config/nightly-review/env <<'EOF'
export CLAUDE_CODE_OAUTH_TOKEN=<token from setup-token>
export TG_BOT_TOKEN=<your bot token>   # optional, see note below
EOF
chmod 600 ~/.config/nightly-review/env
```

The script now sources that file if it exists. (`ANTHROPIC_API_KEY` works
there too if you'd rather use an API key.)

## Cause 2: `status` is a read-only variable in zsh (why you never got a failure note)

```
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

In zsh, `$status` is a built-in read-only alias for `$?`. The line
`status=$?` is a fatal error, so the script exits with code 1 right there,
before the `if` that would have called `notify.sh`. That is why you got no
"FAILED" message either, and why the last exit code is 1. Confirmed with:
`zsh -c 'status=1'` → `read-only variable: status`, rc=1.

**Fix:** renamed the variable to `rc`.

## Other hardening in `bin/nightly-review.zsh` / `bin/notify.sh`

- **Catch-all failure note:** a `TRAPEXIT` handler sends a "FAILED" message
  for any non-zero exit that hasn't already sent one, so an unexpected
  error can't end the run silently again.
- **The failure message includes the last part of the stderr log**, so you
  can see the reason (e.g. "Not logged in") on your phone.
- **Permissions in `-p` mode:** headless mode can't ask for approval, so
  once login works the agent would still be blocked from running
  `git log`/`git show`. Those (plus Read/Grep/Glob) are now pre-approved
  with `--allowedTools`. None of these tools can write files.
- **`notify.sh`:** sources the same env file, so `TG_BOT_TOKEN` doesn't have
  to come from the Keychain. It was only ever tested by hand, and
  `security find-generic-password` can fail in a launchd context (for
  example if the Keychain is locked at 02:30). It also uses `curl --fail`,
  so a Telegram API error now gives a non-zero exit instead of being
  ignored.

## Verified

I ran it locally with a stubbed `claude` and notifier under a fake `$HOME`:
- claude fails → `nightly review FAILED (exit 1): Not logged in · Please run /login`
- claude succeeds → `nightly review done: <summary>`
- repo missing → `nightly review: repo missing`

Not verified here: the real launchd run, real Claude auth and real Telegram
delivery. To test after creating the env file:
`launchctl kickstart -k gui/$UID/com.vk.nightly-review`. You don't need to
reload the plist, because it didn't change.
