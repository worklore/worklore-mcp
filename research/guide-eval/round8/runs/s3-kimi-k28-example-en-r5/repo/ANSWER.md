# Why the nightly job was silent

The job ran perfectly on schedule every night and failed identically every time.
Two stacked bugs, one that made it fail and one that made it mute:

## Bug 1 — the agent can't log in under launchd (why every run failed)

`Library/Logs/nightly-review.err` contains, for every one of the 6 runs
(`runs = 6` in `launchctl-print.txt`, `last exit code = 1`):

```
Not logged in · Please run /login
```

The plist's `EnvironmentVariables` sets only `PATH`. With no `USER` in the
environment, the headless CLI can't resolve its login from the keychain, so it
dies immediately — before reviewing anything.

**Fix:** added `USER` = `vk` to `EnvironmentVariables` in
`Library/LaunchAgents/com.vk.nightly-review.plist`.

## Bug 2 — zsh `status` is read-only (why you never heard about it)

`bin/nightly-review.zsh` had:

```zsh
claude -p "$PROMPT" --output-format text > "$OUT"
status=$?
```

In zsh, `status` is a read-only special variable. The assignment kills the
script on the spot — the second error line in the log,
`/Users/vk/bin/nightly-review.zsh:19: read-only variable: status`. That line
sat between the agent call and the failure notification, so the job failed and
then the messenger died before speaking. (12 log lines = 6 runs × 2 errors;
`nightly-review.out` is empty; every run ended the same way.)

**Fix:** `status=$?` → `rc=$?` in `bin/nightly-review.zsh`. The failure
notification now fires.

## Additional hardening applied

- Prompt is now piped via stdin (`print -r -- "$PROMPT" | claude -p ...`)
  instead of being passed as a multi-line argument in the scheduled context,
  which also removes the "waits on stdin" risk.
- Each run logs its duration (`nightly review finished in ${SECONDS}s` to
  stdout) so a too-fast run is visible as a failure sign.

## Verification

No real Telegram messages were sent and no real agent was run (per the ground
rules). Instead, with a sandboxed `HOME` and a fake `claude` + stub notifier:

- **Success case:** exit 0, empty stderr, success notification containing the
  summary, fresh output `.md` written, duration logged.
- **Forced failure (`claude` exits 1 like the "Not logged in" case):** exit 1,
  agent error in the err log, and — the point of the whole exercise — the
  `nightly review FAILED (exit 1)` notification **was** sent. No
  "read-only variable" error.
- `zsh -n` and `plutil -lint` both pass.

**Remaining manual step (can't be done from this snapshot):** reload the agent
so the plist change takes effect:

```
launchctl bootout gui/$UID/com.vk.nightly-review
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.vk.nightly-review.plist
```

Then `launchctl kickstart -k gui/$UID/com.vk.nightly-review` once and confirm
you get the real summary on Telegram; break the script on purpose once and
confirm you get the failure note. Silence should now be impossible in both
directions.

One residual fragility worth knowing: `bin/notify.sh` runs under `set -eu`
and its first step is a keychain lookup for the Telegram token. If that lookup
ever fails, the notifier itself dies silently. Setting `USER` in the plist
fixes the environment that lookup needs too, but if silence ever recurs, the
keychain read in `notify.sh` is the next place to look.

## Which parts of the colleague's note applied

Applied, in order of how much they mattered:

1. **"First prove whether it ran"** — `launchctl print` (`runs = 6`,
   `last exit code = 1`) was the single most informative artifact. The job was
   never failing to fire; it was failing to speak.
2. **"Read the StandardErrorPath log before theorizing"** — `nightly-review.err`
   contained both errors for all 6 runs and settled the diagnosis outright.
3. **"In zsh never assign to `status` — use `rc=$?`"** — bug 2 verbatim, the
   layer that caused total silence.
4. **"Set `USER` under `EnvironmentVariables` … or the CLI … dies with
   'Not logged in'"** — bug 1 verbatim, from the correction dated 2026-09-30.
5. **"Pass prompts … via stdin rather than multi-line arguments"** — applied as
   hardening; the log can't confirm or deny a prompt-parsing problem here
   because the login failure happened first, but the trap is real and the fix
   is free.
6. **"Log each run's duration"** and **"put the failure notification as close
   to the failure path as possible, and test it by forcing a failure once"** —
   duration logging added; the failure notify already sat immediately after the
   agent call (it was the `status` assignment that orphaned it), and the
   forced-failure test is now part of verification.
7. **The correction about exit-code honesty** ("the exit code tells you *that*
   it ran, not *that it worked*") — applied as the verification standard:
   instead of trusting exit codes, I checked the real outcome (notification
   content, fresh `.md` file) in both directions.

Not applied / ignored:

- The specific reproduction recipe (real `claude`, real Telegram,
  `kickstart` against the live agent). This is a snapshot of a home directory;
  deploying, messaging external services, or touching the live launchd domain
   was out of bounds, so verification used fakes inside the sandbox instead.
  The *shape* of their verification (success notification + forced failure +
  plausible outcome) was kept.
- The "16:50" schedule detail — this job fires at 02:30; irrelevant beyond that.
- `< /dev/null` for stdin — moot once the prompt arrives via a pipe; there is
  no open stdin left to wait on.
