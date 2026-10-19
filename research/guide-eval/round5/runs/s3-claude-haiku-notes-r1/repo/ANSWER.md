# Why the nightly review never reported anything

## Short answer

The job runs on schedule. It fails every night, and the failure report is
never sent, for two stacked reasons:

1. **The notifier is downstream of the failure, and the script kills itself
   before it gets there.** `status=$?` in `bin/nightly-review.zsh` is a
   read-only special parameter in zsh (`status` is an alias for `$?`). The
   assignment aborts the script with exit 1, so the `notify.sh` failure path
   never runs. That is why you got silence and not even a failure message.
2. **The headless agent cannot log in when launchd runs it.** Every run of
   `claude -p` in the error log says `Not logged in · Please run /login`.
   The plist's environment sets only `PATH`, so the CLI has no `USER` (or
   `LOGNAME`) to look up its login in the keychain. Nothing was reviewed.

## Evidence

- `launchctl-print.txt`: `runs = 6`, `last exit code = 1`, schedule
  02:30. Six runs (13–18 Oct) is what the schedule predicts, so launchd is
  not the problem.
- `Library/Logs/nightly-review.err` has 12 lines: six `Not logged in` lines
  from `claude`, and six `nightly-review.zsh:19: read-only variable: status`
  lines from the script. One pair per night.
- `Library/Logs/nightly-review.out` is empty, as expected: the agent's output
  goes to the dated `.md` file, and the notifier prints nothing.
- Reproduced here with zsh 5.9: `zsh -c 'set -u; false; status=$?'` prints
  `read-only variable: status` and exits 1. `rc=$?` works.

## Other silent-failure paths (found while reading, not in the logs)

3. **`notify.sh` could report success while sending nothing.** If the
   keychain lookup for `tg-bot` fails, `: "${TG_BOT_TOKEN:=$(security …)}"`
   leaves the token empty. The script carries on (verified: under `set -e`, a
   failed command substitution inside `${…:=…}` does not abort). The request
   then goes to `…/bot/sendMessage`, Telegram answers 404, and `curl` without
   `-f` exits 0 (verified against a local server: exit 0 without `-f`, exit 22
   with it). Nothing is shown anywhere. This did not cause the current
   silence, because the job never reached the notifier, but it would hide the
   next failure.
4. **No check that the run produced anything.** A run that exits 0 with an
   empty output file was reported as "done" with an empty body.
5. **`claude -p` could block on stdin.** Under launchd, stdin may be an open
   pipe, so the run would hang rather than fail. This was not seen in the
   logs; it is a precaution.

## What I changed

- `bin/nightly-review.zsh`
  - `status` → `rc`. This is the fix for the silence.
  - `< /dev/null` on the `claude` call.
  - Empty-output check, so an empty run is reported as a failure.
  - Duration in both messages. A run that ends in a few seconds means it failed
    before doing any work.
  - The failure message now also points at `nightly-review.err`.
- `bin/notify.sh`
  - Explicit error if the keychain lookup fails or the token is empty.
  - `curl -f`, so HTTP errors from Telegram exit non-zero.
- `Library/LaunchAgents/com.vk.nightly-review.plist`
  - `HOME`, `USER` and `LOGNAME` added to `EnvironmentVariables`.

Verification done here:

- `plutil -lint` on the plist: OK. `zsh -n` and `bash -n` on the scripts: OK.
- The job logic was run with a fake `claude` and a fake notifier, with the
  real script otherwise unchanged. Success, non-zero exit and empty output
  each produced the expected single notification and exit code. Scratch files
  were removed.

Not verified: that `claude` now authenticates under launchd, and that a real
Telegram message arrives. I did not call Telegram or the Claude API from here.

## Caveats

- **The username is a guess.** The paths in the plist and logs say `/Users/vk`
  and `gui/501`, so I set `HOME=/Users/vk`, `USER=vk`, `LOGNAME=vk`. Confirm
  with `id -un` on the machine before loading. A mismatch means the keychain
  lookup still fails.
- **The `USER` fix is the most likely cause of the login failure, not a
  confirmed one.** It matches the "Not logged in" message, and the same fix
  appears in your note on the 16:50 job. If the first run after reloading
  still says `Not logged in`, the next thing to check is the keychain item's
  access settings for the `claude` login.
- `two-bugs-made-my-scheduler-perfectly-silent.md` describes a different
  incident (a 16:50 job, "Input must be provided" error). That error is not in
  this job's logs, so I did not treat its stdin fix as needed here.

## To apply (your machine, not run from here)

Copy the three changed files into place, then reload the job:

```sh
cp bin/nightly-review.zsh ~/bin/nightly-review.zsh
cp bin/notify.sh ~/bin/notify.sh
cp Library/LaunchAgents/com.vk.nightly-review.plist ~/Library/LaunchAgents/
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
launchctl kickstart -k gui/$UID/com.vk.nightly-review
```

Then check, in this order:

1. `launchctl print gui/$UID/com.vk.nightly-review`: `last exit code = 0`.
2. `~/Library/Logs/nightly-review-$(date +%F).md` exists and has content, and
   the run took more than a few seconds.
3. The Telegram success message arrived.
4. Optionally, force a failure once (for example, rename `~/projects/shop`
   for a run) and confirm the failure message arrives.
