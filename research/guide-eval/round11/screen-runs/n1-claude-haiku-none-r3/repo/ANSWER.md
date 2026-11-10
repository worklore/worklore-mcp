# Why every run-vibe.sh run exits in about a second

## Cause

Vibe looks up a key for its default `mistral` provider even when the active model uses OpenRouter. It reads that
key from the macOS Keychain by running `/usr/bin/security`. The sandbox profile `agent.sb` denies
`process-exec` of `/usr/bin/security`, so the exec fails with `EPERM`. Vibe does not catch that error, so the
process dies at startup with exit 2 before any model request is made.

The chain, as found in the installed Vibe 3.1.0 (`vibe/`):

1. `core/config/vibe_schema.py`: `resolve_mistral_api_key()` calls `get_mistral_provider()`. Our `config.toml`
   defines only `openrouter`, but the built-in `mistral` provider is still in the list, so it is found and used.
2. `resolve_api_key("MISTRAL_API_KEY")` (`utils/api_keys.py`) reads the environment first. The variable is unset
   in the run's `env -i` environment, so it falls through to `get_api_key_from_keyring()`.
3. `utils/keyring.py` `_run_security()` runs `/usr/bin/security`. It catches only `FileNotFoundError` and
   `TimeoutExpired`, so `PermissionError: [Errno 1] Operation not permitted: '/usr/bin/security'` propagates
   and kills the run.

The OpenRouter key was never the problem: `OPENROUTER_API_KEY` resolves from the environment without touching
the Keychain.

Reproduced inside the same sandbox profile, with no network calls:

- `get_api_key_from_keyring('MISTRAL_API_KEY')` raises `PermissionError [Errno 1] Operation not permitted: '/usr/bin/security'`.
- `resolve_api_key('OPENROUTER_API_KEY')` returns the key.

This matches `logs/last-run.err`:

```
Reading API keys from the macOS Keychain (set them as environment variables to skip this)
Error: [Errno 1] Operation not permitted: '/usr/bin/security'
```

## Fix

`run-vibe.sh` now passes `VIBE_TEST_DISABLE_KEYRING=1` into the sandboxed environment. Vibe's keyring module checks
this variable and returns `None` for every Keychain read, so the `MISTRAL_API_KEY` lookup returns cleanly and the
Keychain is never touched.

I did not fix this by allowing `/usr/bin/security` in `agent.sb`. That would let the agent run the Keychain client,
which the profile is meant to block. The sandbox profile is unchanged.

The variable name says "TEST", but it is read by production code (`vibe/utils/keyring.py`, and
`vibe/setup/auth/_oidc_credentials.py`). It is the only switch Vibe has for skipping the Keychain. If a future Vibe
release renames it, the symptom will return; re-check with the reproduction above.

## Verification

- With the variable set, the keyring read inside the sandbox returns `None` instead of raising.
- `OPENROUTER_API_KEY=dummy-invalid-key-test ./run-vibe.sh "say hi" <dir>` now gets past startup. It fails with
  `Error: Invalid API key (from env var OPENROUTER_API_KEY)`, which is the expected result for a dummy key. No
  Keychain error, no `PermissionError`. That run used a dummy key, so no real run was made.
- A real run still needs your real `OPENROUTER_API_KEY`. I did not make a live model call.
- The tracked `logs/last-run.*` files were restored to the original failure logs after testing.
