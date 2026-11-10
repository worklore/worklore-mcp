# Cause and fix

Vibe exits during startup because it tries to read a Mistral API key from the macOS Keychain. The launcher starts Vibe with `env -i` and passes `OPENROUTER_API_KEY`, but no `MISTRAL_API_KEY`. The recorded stderr shows the Keychain lookup followed by `Operation not permitted: '/usr/bin/security'`; `agent.sb` deliberately denies that executable. Vibe exits with code 2 before writing an export or contacting the configured OpenRouter provider.

I added `MISTRAL_API_KEY=unused` to the `env -i` invocation in `run-vibe.sh`. This supplies a non-secret value for Vibe's Mistral-key startup check while the configured `devstral` model continues to use the OpenRouter provider and `OPENROUTER_API_KEY`. The Keychain denial remains in place.

The colleague's note applies to the Keychain error, its cause, and the placeholder-key fix. Its suggestions to use a Vibe `.env` file or `VIBE_TEST_DISABLE_KEYRING` were unnecessary here. I did not use its suggestion to allow `/usr/bin/security`, since that would weaken the intended sandbox boundary.

`bash -n run-vibe.sh` verifies shell syntax. The sandbox still rejects `/usr/bin/security list-keychains` (exit 71). A live Vibe run could not be verified because `OPENROUTER_API_KEY` is unset in this environment; running with a valid key would also contact OpenRouter, which is outside the requested local-only work.
