# Why run-vibe.sh exited in under a second

## Cause

Vibe's Rust front end (`vibe/_bin/vibe-rs`, the binary the `vibe` command execs) looks for `MISTRAL_API_KEY` at
start-up, even when the active provider is OpenRouter. If the variable is not in the environment, it runs
`/usr/bin/security find-generic-password -s ai.mistral.vibe ...` to read the Keychain. `agent.sb` denies
`/usr/bin/security` on purpose, so the call fails with `Operation not permitted`, and Vibe exits with code 2
before it does any work. `logs/last-run.err` shows this:

    Reading API keys from the macOS Keychain (set them as environment variables to skip this)
    Error: [Errno 1] Operation not permitted: '/usr/bin/security'

The OpenRouter key was never the problem. The config's `api_key_env_var = "OPENROUTER_API_KEY"` was fine.

## Fix

`run-vibe.sh` now passes `VIBE_TEST_DISABLE_KEYRING=1` on the `env -i` line. Vibe then skips the Keychain read and
treats `MISTRAL_API_KEY` as absent. The sandbox profile is unchanged, and `/usr/bin/security` stays denied.

## Parts of the colleague's note

- **Applied:** the diagnosis. The stderr lines match, the `/usr/bin/security` denial is the failure, and the
  sandbox must stay as it is. Setting an env var on the `env -i` line, not exporting it first, is also right.
- **Applied, with a different variable:** the note's last option, `VIBE_TEST_DISABLE_KEYRING`. I use it as the fix
  instead of `MISTRAL_API_KEY=unused`, for the reason below. The name says "test", but in this build the variable
  does one thing: it turns off the keyring read (`utils/keyring.py`, `_is_keyring_disabled`). The Rust binary has the
  same string next to the `/usr/bin/security` call. It is still an undocumented switch, so re-check it after upgrades.
- **Not applied: `MISTRAL_API_KEY=unused`.** The note says Vibe "never sends it anywhere, because the active
  provider is OpenRouter." That is not right. The default config union-merges a Mistral provider
  (`DEFAULT_PROVIDERS`, `api_key_env_var = MISTRAL_API_KEY`) into your OpenRouter config. With a non-empty
  `MISTRAL_API_KEY`, that provider counts as credentialed. Checked inside the sandbox, `resolve_api_key("MISTRAL_API_KEY")`
  returns `unused`. From there:
  - `WebSearch.is_available()` is true, so the `web_search` tool is offered to the model. Its queries go to
    `api.mistral.ai`, a different company, which is what the sandbox is meant to prevent.
  - The utility-model path (title generation, smart approve) uses the Mistral provider's fast model, so
    conversation text can go to Mistral too.
  With `VIBE_TEST_DISABLE_KEYRING=1` and no `MISTRAL_API_KEY`, the same check returns `None`, so none of this is
  enabled. The placeholder would not leak a real key (there is none), but it would send content to Mistral.
- **Not used:** the `.env` in `VIBE_HOME` option. It would also set `MISTRAL_API_KEY`, which has the same problem.

## Verification

- Before the fix, with `OPENROUTER_API_KEY` set to a dummy value: exit 2, the two stderr lines above, no export.
- After the fix, same sandbox, same dummy key: the Keychain line is gone. Vibe reaches OpenRouter and fails there
  with `Error: Invalid API key (from env var OPENROUTER_API_KEY)`. Exit 1. That is the expected result for a wrong key.
- `sandbox-exec -D HOME=... -f agent.sb /usr/bin/security list-keychains`: `Operation not permitted`, exit 71.
- The Python check above: `MISTRAL_API_KEY` unset with `VIBE_TEST_DISABLE_KEYRING=1` → `None`; set to `unused` → `unused`.

The test run made one request to OpenRouter with a dummy key and the prompt "say hi". I restored the tracked
`logs/last-run.*` files to their original contents and removed the test export folder.

## Not verified

I did not watch network traffic, so "no Mistral calls" rests on reading the code plus the resolution check above.
I did not run with a real OpenRouter key, so a successful end-to-end completion is untested.
