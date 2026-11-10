# Cause and fix

Vibe 3.1.0 tries to inspect the macOS Keychain during startup, even though the OpenRouter key is supplied through `OPENROUTER_API_KEY`. It runs `/usr/bin/security` for that inspection. `agent.sb` deliberately forbids that executable, so the subprocess raises `Operation not permitted` and Vibe exits with code 2 before handling the prompt.

`run-vibe.sh` now passes `VIBE_TEST_DISABLE_KEYRING=1` into Vibe's allowlisted environment. In this installed Vibe version, that switch makes its Keychain reads return no credential without launching `/usr/bin/security`. The OpenRouter key still comes from `OPENROUTER_API_KEY`, and the sandbox continues to deny Keychain access.
