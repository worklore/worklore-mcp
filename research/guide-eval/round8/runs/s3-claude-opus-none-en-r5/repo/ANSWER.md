# Why the nightly review never reported anything

The job *does* run. `launchctl-print.txt` shows `runs = 6` (one per night,
2026-10-12 → 10-18) and `last exit code = 1`, and `nightly-review.err` holds
six identical pairs of lines. Two bugs stack up, and the second one hides the first.

## 1. The script dies before it can notify: `status` is read-only in zsh (why there was no failure note)

```
/Users/vk/bin/nightly-review.zsh:19: read-only variable: status
```

In zsh, `$status` is a built-in, read-only alias for `$?`. `status=$?` is
a fatal error in a non-interactive script: zsh aborts right there with exit 1.
That's the `last exit code = 1` launchd reports. Both `"$NOTIFY" ...` calls
come after that line, so neither the failure note nor the summary was ever sent.
(It works in bash, which is why it looks fine.) Reproduced with
`zsh -c 'set -u; false; status=$?; echo after'`, which prints the same error and exits 1.

**Fix:** renamed it to `rc`.

## 2. `claude` isn't authenticated in the launchd environment (why it fails at all)

```
Not logged in · Please run /login
```

launchd runs the job with a minimal environment: just the plist's `PATH` plus
`XPC_SERVICE_NAME`. It doesn't read `~/.zshrc`/`~/.zprofile`. Whatever
authenticates `claude` in your Terminal (for example an `ANTHROPIC_API_KEY`
exported from your shell profile, or a login the background session can't
reach) isn't available to the agent, so `claude -p` exits non-zero right away.
You'd then hit bug #1 every night.

**Fix:** the script now reads a long-lived token from the Keychain when no auth
variable is set. One-time setup, which you have to do yourself:

```sh
claude setup-token                      # prints a long-lived OAuth token
security add-generic-password -a "$USER" -s claude-code-oauth -w '<token>'
```

(Or export `ANTHROPIC_API_KEY` from the Keychain the same way if you use API-key billing.)

## Other changes (hardening, not root causes)

- **A failure path can't stay silent anymore.** A `TRAPEXIT` sends a
  "FAILED unexpectedly" note if the script exits by any route without
  notifying. Failure notes point to `nightly-review.err`, because `claude`
  writes its errors to stderr, not to the `.md` file.
- **Headless permissions.** `claude -p` can't answer permission prompts, so
  without pre-approval it couldn't even run `git log`. The script now passes
  `--allowedTools` for read-only tools only (`Read`, `Grep`, `Glob`,
  `git log/show/diff`). That also enforces "do not modify any file".
- **`notify.sh` reported Telegram errors as success.** `curl -sS` exits 0 on
  HTTP 4xx/5xx (bad token, wrong chat id). It now uses `--fail-with-body` and
  writes an error line to stderr, which lands in `nightly-review.err`.

## Verification

- `zsh -n` / `bash -n` pass on both scripts.
- I ran the fixed script against stubbed `claude`/`notify.sh`/`security`. A
  failing `claude` now sends "nightly review FAILED (exit 1)…" and exits 1. A
  succeeding one sends "nightly review done: …" and exits 0.
- Not done (outside this folder / external): creating the token, reloading the
  agent, a real Telegram send. After the token setup, test with
  `launchctl kickstart -k gui/$UID/com.vk.nightly-review`. The plist itself
  didn't need changes.
