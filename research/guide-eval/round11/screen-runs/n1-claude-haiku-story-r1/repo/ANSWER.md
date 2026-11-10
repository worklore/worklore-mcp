# Why every run exits at once

## Cause

Vibe reads the Keychain for `MISTRAL_API_KEY` even though the active provider is OpenRouter.
The sandbox denies `/usr/bin/security`, so that read fails with `Operation not permitted` and Vibe exits 2 before it reaches the provider.

Evidence:

- The launcher's stderr is `Error: [Errno 1] Operation not permitted: '/usr/bin/security'`, and `logs/last-run-export/export.json` records `infrastructure_failure` with the same error.
- A `sitecustomize` hook that logs every `subprocess.run` call, run inside the same sandbox, shows the call:
  `/usr/bin/security find-generic-password -s ai.mistral.vibe -a MISTRAL_API_KEY -w`.
  The stack goes `session setup -> mistral_credentials() -> resolve_api_key_with_origin("MISTRAL_API_KEY") -> get_api_key_from_keyring()` (installed Vibe 3.1.0, `vibe/utils/api_keys.py:112`, `vibe/utils/keyring.py`).
- Cause of the Mistral lookup: `get_mistral_provider()` falls back to the built-in Mistral provider when the active provider is not Mistral. Its key is read only when `MISTRAL_API_KEY` is unset in the environment (`api_keys.py:112`: `keyring_value = None if env_value else get_api_key_from_keyring(env_key)`).

The OpenRouter key was never the problem.

## Fix

1. `run-vibe.sh`: add `MISTRAL_API_KEY=unused` to the `env -i` line, next to `OPENROUTER_API_KEY`. With a non-empty value the Keychain is never read. The sandbox is unchanged.
2. `vibe/config.toml`: add `disabled_tools = ["web_search"]`. This is an addition beyond the colleague's note (see below).

## Verified

- Before the fix (dummy `OPENROUTER_API_KEY`): exit 2, `/usr/bin/security` denied. Reproduced.
- After the fix, same sandbox: exit 1 with `Error: Invalid API key (from env var OPENROUTER_API_KEY)`. Startup gets through, the Keychain is not touched (0 `security` calls in the hook trace), and Vibe reaches the provider.
- `sandbox-exec -D HOME=... -f agent.sb /usr/bin/security list-keychains` still fails with `Operation not permitted`.
- `disabled_tools` parses as `['web_search']`, and the registered name of the web search tool is `web_search`.

Not verified: a successful model reply. I had no real OpenRouter key, so the runs stopped at provider auth. I also did not capture network traffic, so "nothing is sent to Mistral" rests on the code path, not on a packet capture. The `disabled_tools` effect is verified by config parse and name match, not by listing the tools inside a running session.

## Colleague's note: what applied

- **Applied:** the cause is the Keychain read of `MISTRAL_API_KEY`, denied because the sandbox blocks `/usr/bin/security`. Confirmed in the installed 3.1.0 code and by trace.
- **Applied:** the fix is `MISTRAL_API_KEY=unused` on the `env -i` line, not a loosened sandbox. Confirmed by the run above.
- **Applied:** the verification steps (startup passes, provider error text, `security list-keychains` still denied).
- **Not applied:** `VIBE_TEST_DISABLE_KEYRING=1`. It is a test switch and I did not rely on it.
- **Not applied:** a `.env` in `VIBE_HOME`. The env var is enough, and the launcher already passes env.
- **Not matched:** "no export folder is written". A failed run did write `export.json` in my reproduction.
- **Not matched:** the exact stderr line `Reading API keys from the macOS Keychain ...`. It does appear in the output of the installed build when I reproduce, but grep finds no such string in the package source, so I did not locate where it is printed. It does not change the cause.
- **Added by me:** `disabled_tools = ["web_search"]`. With a placeholder `MISTRAL_API_KEY`, `WebSearch.is_available()` returns true, so the model could call a tool that sends query text to Mistral's API. The note does not mention this. Disabling the tool keeps the sandbox boundary intact.

## Caveats

- `MISTRAL_API_KEY=unused` is a placeholder, not a credential. Any future code path that uses that key for a Mistral call would send the placeholder, not a real key, and would fail.
- Repo state: `run-vibe.sh` and `vibe/config.toml` are modified in the working tree. Nothing is committed. `logs/` is restored to its committed state (the original failing run); my test runs were in scratch folders and removed.
