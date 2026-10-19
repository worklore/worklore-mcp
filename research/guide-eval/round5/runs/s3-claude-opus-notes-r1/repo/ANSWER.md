# Why the nightly review never reported anything

The job **was** running. `launchctl-print.txt` shows `runs = 6` (one run each
night from 10-13 to 10-18) and `last exit code = 1`. Every run left the same two
lines in `Library/Logs/nightly-review.err`:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

Two bugs stacked on top of each other:

1. **The review fails: `claude` is "Not logged in" under launchd.** The plist's
   `EnvironmentVariables` sets only `PATH`. With no `USER`, the CLI can't find
   its login credentials in the keychain, so it quits straight away.
   (`.out` is empty because nothing ever ran.)

2. **The failure report dies too: `status=$?` on line 19.** In zsh, `status` is
   a read-only built-in variable. Assigning to it is a fatal error, so the
   script exits with code 1 right there. That line sits between the `claude`
   call and the `notify.sh` call, so the "FAILED" message is never sent.
   Bug 1 makes the job fail, and bug 2 stops it from telling you.

## Fixes made

`Library/LaunchAgents/com.vk.nightly-review.plist`
- Added `USER=vk`, `HOME=/Users/vk` and `LANG=en_US.UTF-8` to
  `EnvironmentVariables`. `USER` fixes "Not logged in". `LANG` makes zsh
  handle text as UTF-8 when it shortens the summary to 300 characters.

`bin/nightly-review.zsh`
- `status=$?` became `rc=$?`.
- The prompt now goes in through stdin (`print -r -- "$PROMPT" | claude -p ...`).
  That avoids passing a multi-line argument, and `claude` can't sit waiting on
  an open stdin.
- Every run writes its exit code and how long it took to the `.err` log. A run
  that ends after a few seconds means it failed before doing any work.
- If `claude` exits 0 but the output file is empty, that is now reported as a
  failure.
- The success summary is shortened by characters, not bytes. The old
  `head -c 300` could cut a multi-byte character in half, and Telegram rejects
  text that isn't valid UTF-8.
- If `notify.sh` itself fails, that is now written to the `.err` log instead of
  vanishing.

`bin/notify.sh`
- `curl -sS` became `curl -fsS --retry 2`. Before, if Telegram rejected the
  message (HTTP 400/401), curl still exited 0, so that failure was silent too.

I checked it locally with a fake `claude` and a fake notifier: a "Not logged in"
failure now sends the FAILED message and exits 1, and a successful run sends
the summary, including non-ASCII text.

## What you need to do on the real machine

```sh
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
tail ~/Library/Logs/nightly-review.err
```

Then check three things: you got a Telegram message, the latest
`nightly-review-YYYY-MM-DD.md` file has a real review in it, and the run took a
plausible amount of time. If it still says "Not logged in", the login isn't
reachable from launchd. In that case, run `claude setup-token` and put the
token in the plist as `CLAUDE_CODE_OAUTH_TOKEN` (or have the script read it
from the keychain). Also break the job on purpose once and confirm the FAILED
message arrives.
