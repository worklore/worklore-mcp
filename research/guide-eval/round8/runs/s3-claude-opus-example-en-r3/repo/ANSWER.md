# Why nightly-review never reported anything

## It did run
`launchctl-print.txt` (captured 2026-10-18) shows `runs = 6`, `last exit code = 1`.
That's one run per night from 10-13 to 10-18. launchd was working fine. The script
was failing, and it failed in a way that also stopped the report. `nightly-review.err`
shows the same two lines for every one of the six runs:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

## Cause 1: `claude -p` is "Not logged in" under launchd
The job's environment only contains `PATH` (and `XPC_SERVICE_NAME`; see the
`environment` block). `USER` isn't set, so the CLI can't find its login in the
keychain and exits 1 immediately. A run that fails this way does no work at all.
**Fix:** the plist's `EnvironmentVariables` now sets `USER`, `LOGNAME` and `HOME`
to `vk` / `/Users/vk`.

## Cause 2: `status=$?` killed the script before it could report (why nothing arrived)
In zsh, `status` is a read-only special parameter. Assigning to it is a fatal error,
and zsh exits with code 1, which is the `last exit code = 1`. That line (19) sits
between the `claude` call and the `notify.sh` call, so the failure notifier never
ran. Note that this would have happened on success too: even with a working login,
you would never have gotten a summary. I reproduced it with `zsh -c 'status=1'`,
which prints `read-only variable: status` and exits 1.
**Fix:** use `rc=$?`.

## Other hardening (not causes, but they stop this from going silent again)
- **The prompt goes in on stdin** (`print -r -- "$PROMPT" | claude -p ...`). That
  avoids multi-line argument parsing and means `claude` never waits on an open stdin.
- **Exit 0 isn't treated as success on its own.** If the output file is empty, the
  script sends a failure notification.
- **Each run logs a start time, claude's exit code and how long it took** to the
  `.err` log, and the duration is included in the Telegram message. A run that ends
  in a few seconds is a red flag.
- **All notifications go through a `notify()` wrapper.** If Telegram itself fails,
  the wrapper writes that to the log.
- **`notify.sh` uses `curl --fail-with-body --max-time 30`.** Before, an HTTP error
  from the Telegram API (bad token, wrong chat id) was ignored and the script still
  exited 0.

## What I verified here
`plutil -lint` passes on the plist, and `zsh -n` / `bash -n` pass on the scripts. I
ran the new script with stubs standing in for `claude` and `notify.sh` in three
cases: claude fails with "Not logged in", claude succeeds, and claude exits 0 with
no output. Each case produced the right notification and exit code. I couldn't test
the real launchd, keychain or Telegram path from this snapshot.

## What you still need to do on the Mac
1. Copy the files into place, then reload the job:
   `launchctl bootout gui/$UID/com.vk.nightly-review; launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist`
   (if you edit the plist in place, `kickstart` won't pick up the new environment).
2. `launchctl kickstart -k gui/$UID/com.vk.nightly-review`, then check:
   `last exit code = 0`, today's `nightly-review-YYYY-MM-DD.md` exists and isn't
   empty, the logged duration looks reasonable (not about 1s), and the summary
   arrived on Telegram.
3. If it still says "Not logged in", run `claude` once interactively, or set up a
   long-lived token with `claude setup-token` and put it in the plist environment as
   `CLAUDE_CODE_OAUTH_TOKEN`.
4. Break it on purpose once (for example, point `REPO` somewhere that doesn't exist)
   and confirm the failure notification arrives.

## What applied from the colleague's note
- **Applied:**
  - Checking `launchctl print` first: runs and exit code showed the job did run.
  - Reading the stderr log before guessing at causes.
  - The `status` read-only bug. Same bug, same position between the agent call and
    the notifier.
  - "Not logged in" fixed by setting `USER` in `EnvironmentVariables`.
  - "Exit code isn't proof it worked": the script now checks the output and logs
    the duration.
  - Notifying on every failure path, and testing by forcing a failure.
- **Didn't apply as a cause, used only as hardening:**
  - The "Input must be provided…" prompt-not-received error. It doesn't appear in
    this log.
  - The stdin hang (`< /dev/null`). launchd gives jobs `/dev/null` as stdin, and
    the job exited instead of hanging. I switched to piping the prompt in anyway,
    which covers both.
- **Not relevant:** the 16:50 schedule and the specifics of the watchdog example.
