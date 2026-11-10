# Why every run-vibe.sh run exits in about a second

**Cause:** at startup Mistral Vibe looks up `MISTRAL_API_KEY` in the macOS Keychain by running
`/usr/bin/security`. The run's `agent.sb` sandbox denies `process-exec` for that binary, so the exec fails with
`PermissionError: [Errno 1] Operation not permitted: '/usr/bin/security'`. Vibe's keyring code
(`vibe/utils/keyring.py`, `_run_security`) only wraps `FileNotFoundError`, so the `PermissionError` is not turned
into a handled error and Vibe exits with status 2 before it makes any model call. `logs/last-run.err` shows exactly
this.

Vibe asks for `MISTRAL_API_KEY` even though the configured provider is OpenRouter, which reads `OPENROUTER_API_KEY`
from the environment. The OpenRouter key was never the problem: `resolve_api_key("OPENROUTER_API_KEY")` returns
the env value without touching the Keychain.

**Reproduced:** under the same `agent.sb` profile, `resolve_api_key("MISTRAL_API_KEY")` raises the same
`PermissionError`, and `resolve_api_key("OPENROUTER_API_KEY")` succeeds.

**Fix:** `run-vibe.sh` now passes `VIBE_TEST_DISABLE_KEYRING=1` into the sandboxed environment. Vibe's keyring
module honours this switch: `get_api_key_from_keyring` returns `None` without calling `security`. I checked that
`MISTRAL_API_KEY` then resolves to `None` under the sandbox with no error. I did not loosen `agent.sb`, so the
Keychain and the real home directory are still unreachable.

**Verification:** with a placeholder `OPENROUTER_API_KEY=dummy-test-key`, the script now gets past startup and fails
only at OpenRouter's auth check (`Invalid API key (from env var OPENROUTER_API_KEY)`, exit 1). Startup is fixed. I did
not run a real prompt, because `OPENROUTER_API_KEY` is not set in the shell I worked in. With your real key set,
`./run-vibe.sh "say hi" /tmp/x` should now run normally.

**Notes:**
- The stderr text `Reading API keys from the macOS Keychain (...)` in the old log does not appear in the installed
  Vibe 3.1.0 source. The traceback logic matches, so the log probably came from a slightly different build. The fix
  holds either way, because the switch is checked before any Keychain read.
- `VIBE_TEST_DISABLE_KEYRING` is a test-oriented name. It is the only switch I found that stops the Keychain read
  without changing the installed package or the sandbox. If Vibe is upgraded, check that it still honours it.
- Alternatives I rejected: allowing `/usr/bin/security` in `agent.sb` (widens the sandbox), or setting a dummy
  `MISTRAL_API_KEY` (hacky, and it could be sent somewhere). Fixing `_run_security` in the installed package would
  be the upstream fix, but it is outside this directory.
- `logs/last-run.out` and `logs/last-run.err` now hold the output of the placeholder-key test run.
