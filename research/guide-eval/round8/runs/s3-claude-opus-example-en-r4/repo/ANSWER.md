# Why the nightly review has been silent

## launchd is running it. The script is what fails.

`launchctl-print.txt` (captured 2026-10-18) shows `runs = 6` and `last exit code = 1`. That is one run per night from 10-12 to 10-17. `Library/Logs/nightly-review.err` has the same two lines for each of the six runs:

```
Not logged in · Please run /login
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

So there are two bugs, one on top of the other.

### Cause 1: `claude -p` fails with "Not logged in"

The plist's `EnvironmentVariables` set only `PATH`. Under launchd, `USER` is not set (it is missing from the `environment` block in the launchctl output too). Without it the Claude CLI can't find its login in the keychain, so it exits non-zero straight away and writes nothing. The review never ran, and each night's `nightly-review-<date>.md` is empty.

**Fix:** I added `USER=vk` and `LOGNAME=vk` to `EnvironmentVariables` in `Library/LaunchAgents/com.vk.nightly-review.plist`.

### Cause 2: `status=$?` kills the script before it can report anything (this is why nothing reached you)

In zsh, `status` is a read-only special variable (it is the same as `$?`). Assigning to it is a fatal error: the script stops on line 19 with exit code 1. That is the `last exit code = 1` launchd recorded. The `"$NOTIFY" "nightly review FAILED ..."` call comes after that line, so it never ran. You got no summary and no failure note. I checked this with `zsh -c 'status=1'`, which prints `read-only variable: status` and exits with 1.

**Fix:** use `rc=$?` instead.

## Other changes to `bin/nightly-review.zsh` (hardening, not causes)

- `claude -p ... < /dev/null`: the prompt is passed as an argument, so stdin is explicitly closed and the CLI can't wait on it. launchd already gives stdin as `/dev/null` by default, so this wasn't the bug here.
- A `zshexit` safety net: if the script dies before it reports (for example, someone puts `status=` back), it still sends a "DIED unexpectedly" note.
- The script logs the start time, `USER`, claude's exit code and how long the run took to the `.err` log. A run that takes a few seconds means it failed before doing any work.
- If claude exits 0 but the output file is empty, that now counts as a failure. A green exit code with nothing produced is not a success.
- The failure message now includes the end of the stderr log, so you can see on Telegram why it failed.
- `bin/notify.sh`: `curl -sS` became `curl -fsS`, so a Telegram API error (bad token, bad chat id) gives a non-zero exit and a line in the log instead of failing quietly.

I tested this locally with stub `claude` and `notify.sh` on the four paths: claude fails, claude succeeds, claude exits 0 with empty output, and the old `status=` line put back. Each path sent exactly one notification. I have not run it under the real launchd or against Telegram.

## What you need to do on the Mac

```sh
launchctl bootout gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
```

You need to bootout and bootstrap again because launchd only reads `EnvironmentVariables` when the plist is loaded. Then check all of these:

- `launchctl print gui/$UID/com.vk.nightly-review` shows `last exit code = 0`.
- Today's `~/Library/Logs/nightly-review-YYYY-MM-DD.md` is new and not empty.
- The `.err` log shows a plausible run time, not 0–3 s.
- The summary arrived on Telegram.

After that, break it on purpose once (for example, set `REPO` to a path that doesn't exist, or kickstart with `USER` removed) and check that the failure note arrives too.

If "Not logged in" still shows up after adding `USER`, run `claude` once by hand in a GUI terminal to make sure the keychain login exists. If the API-key route suits you better, you could set `ANTHROPIC_API_KEY` for the job instead.

One more possible problem: `notify.sh` reads the bot token with `security find-generic-password`. That works in a GUI launchd agent while you're logged in, but if the keychain is locked at 02:30 the notifier itself will fail. With `curl -f` and the new logging, that failure will now appear in `nightly-review.err` rather than getting lost.

## Which parts of the colleague's note applied

**Applied:**
- "First prove whether it ran with `launchctl print`." Yes: runs = 6, last exit code = 1. The job had been firing all along.
- "Read the StandardErrorPath log before theorizing." The log had both causes in it.
- "zsh `status` is read-only, and the failure reporter sits downstream of the failure." This is exactly cause 2, on the same kind of line.
- "Set `USER` in the plist or the CLI dies with 'Not logged in'." This is exactly cause 1.
- The correction that an exit code shows the job ran, not that it worked. That's why I added the empty-output check and the run-time logging.
- "Log each run's duration, put the failure notification early, test it by forcing a failure." I did these (the forced-failure test was with stubs here; on the Mac it's your step).

**Did not apply:**
- "The prompt isn't received; pipe it via stdin." Here the prompt did arrive: the error was "Not logged in", not "Input must be provided...". I kept the argument and only added `< /dev/null` as a precaution, which the note itself offers as an option. launchd already supplies `/dev/null` as stdin, so it wasn't a cause.
- The 16:50 schedule and the other details of their setup are specific to them. This job runs at 02:30.
