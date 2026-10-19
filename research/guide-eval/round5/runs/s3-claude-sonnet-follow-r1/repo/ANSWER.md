# Why nightly-review was silent

`launchctl-print.txt` shows `runs = 6`, `last exit code = 1`: the job fired every night
and failed. The logs (`Library/Logs/nightly-review.err`) show two stacked causes:

1. **`Not logged in · Please run /login`** – under launchd the plist's environment had
   only `PATH`; no `USER`, so the `claude` CLI could not find its login in the keychain
   and died immediately. Fix: add `USER=vk` to `EnvironmentVariables` in the plist.
   (Also: pass the prompt via stdin, `print -r -- "$PROMPT" | claude -p ...`, rather than a
   multi-line argument.)
2. **`nightly-review.zsh:19: read-only variable: status`** – the script did `status=$?`.
   In zsh `status` is a read-only builtin, so assigning to it aborts the script before it
   reaches the failure notification. The failure reporter was downstream of the failure,
   so Telegram never heard anything. Fix: use `rc=$?`.

## Changes
- `bin/nightly-review.zsh`: `rc` instead of `status`; prompt piped via stdin; failures go
  through a `fail()` helper that also logs to stderr; logs duration/bytes; treats empty
  output (exit 0 but no work) as a failure; success message includes duration.
- `Library/LaunchAgents/com.vk.nightly-review.plist`: added `USER`.

## To apply and verify (on the real machine; I could not run launchd here)
```
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
launchctl print gui/$UID/com.vk.nightly-review   # last exit code = 0
```
Confirm the output file is fresh and non-empty, the run took a plausible time (not a few
seconds), and the Telegram "done" message arrived. Then force a failure once (e.g. rename
the repo path) and confirm the failure message arrives.

Also check: `notify.sh` reads the token from the keychain, so it too relies on `USER`
being set (now fixed). The README says 02:30 while the plist uses 02:30 as well; unchanged.
