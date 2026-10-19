# Why the nightly review never reported anything

## The job runs fine; the script fails and can't tell you
`launchctl-print.txt` shows `runs = 6` and `last exit code = 1`. The job was loaded on 2026-10-12
and has fired every night from the 13th to the 18th, so that's 6 runs. launchd is fine. The
`.err` log has the same two lines for every run:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

So there are two bugs, one on top of the other:

1. **`claude` isn't logged in under launchd (the root cause).** The `environment` block in the
   plist / `launchctl print` only sets `PATH` (plus `XPC_SERVICE_NAME`). There is no `USER`, so
   the CLI can't find its login in the keychain and quits straight away with "Not logged in".
   When you run it by hand your shell sets `USER`, which is why it works for you.
2. **`status=$?` kills the script (why you got no message).** In zsh `$status` is a read-only
   built-in. Assigning to it is a fatal error, so the script died on line 19, after `claude`
   failed and before the `if` that calls `notify.sh`. The failure report was never sent, so
   nothing arrived. (The exit code 1 comes from that fatal assignment.)

The `nightly-review-YYYY-MM-DD.md` files that were made would be empty. `nightly-review.out`
is empty because all output was redirected to `$OUT`.

## Fixes
- `Library/LaunchAgents/com.vk.nightly-review.plist`: added `USER=vk` (and `HOME=/Users/vk`,
  to be explicit) to `EnvironmentVariables`.
- `bin/nightly-review.zsh`:
  - `status=$?` changed to `rc=$?`.
  - The prompt now goes to `claude -p` on stdin (`print -r -- "$PROMPT" | claude -p ...`), so it
    can't hang waiting on stdin and doesn't depend on a multi-line argument.
  - Each run logs its start time, `USER`/`HOME`, the claude exit code and how long it took to
    `nightly-review.err`.
  - Exit 0 with an empty review file is now treated as a failure and reported.
  - `notify` wrapper: if `notify.sh` fails (for example the keychain lookup for the bot token
    or curl fails), a line goes to the `.err` log, so that failure is visible too.

## Verified here (simulation only)
I ran the script under `env -i` (only HOME and PATH, like launchd) with stub `claude`/`notify.sh`:
- the original script with claude failing: **no notification** (the bug reproduces)
- the fixed script with claude failing: FAILED notification, exit 1
- the fixed script with claude exiting 0 and no output: FAILED notification, exit 1
- the fixed script with claude succeeding: "done" notification with the summary, exit 0

`plutil -lint` passes and `zsh -n` passes.

## What you still need to do on the real machine (not done, this is only a snapshot)
1. Copy the two files into place, then
   `launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`
   (plist changes only take effect after reloading).
2. `launchctl kickstart -k gui/$UID/com.vk.nightly-review`, then check: `last exit code = 0`, today's
   `.md` file is non-empty and fresh, the logged duration is believable (tens of seconds or more,
   not 0–2 s), and the Telegram summary arrived.
3. Force a failure once (for example point `REPO` at a missing directory, or rename `claude` in
   PATH) and make sure the FAILED message arrives. If it doesn't, check `.err` for
   `notify.sh failed`. `security find-generic-password` in `notify.sh` needs the login keychain,
   which is available in the gui domain while you're logged in.
4. If it still says "Not logged in" with USER set, run `claude setup-token` and put
   `CLAUDE_CODE_OAUTH_TOKEN` in the environment (not done here, it's a secret).

## Which parts of the colleague's note applied
- **Applied:** check `launchctl print` first (runs/exit code showed the job does run); read the
  stderr log before guessing; **`status` is read-only in zsh, use `rc`** (exactly the
  second bug); **set `USER` in `EnvironmentVariables`, or you get "Not logged in"** (exactly the
  first bug); the failure reporter was after the failure; exit code is not proof of work (now
  checked: empty output means failure, and duration is logged); test the failure path on purpose.
- **Partly / as a precaution:** sending the prompt on stdin / `< /dev/null`. The colleague's error
  "Input must be provided either through stdin or as a prompt argument" **does not appear** in
  this log; here auth failed first. I still switched to stdin because it costs nothing.
- **Didn't apply:** "launchd isn't firing" never was the theory here, and the colleague's
  schedule/labels are theirs. I didn't contact any external service (no real Telegram or claude calls).
