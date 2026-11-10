# Cause and fix

The saved run exited with code 2 before writing an export. Its stderr says Vibe tried to read API keys from the macOS Keychain, then failed to execute `/usr/bin/security`. The launcher uses `env -i` and supplied only `OPENROUTER_API_KEY`; Vibe 3.1.0 also checks for `MISTRAL_API_KEY` at startup even though the configured model uses OpenRouter. With that variable absent, it falls back to the Keychain, which `agent.sb` deliberately blocks.

I added `MISTRAL_API_KEY=unused` to the environment passed directly to Vibe. The configured provider still gets its key from `OPENROUTER_API_KEY`. The sandbox rule denying `/usr/bin/security` remains in place.

The colleague's note applies to the Keychain error, Vibe's startup check for `MISTRAL_API_KEY` with a non-Mistral provider, and the need to put the placeholder on the `env -i` command. Its `.env` and test-switch alternatives were not needed. I did not use the suggestion to allow Keychain access.

`bash -n run-vibe.sh` passes, and `/usr/bin/security list-keychains` is still denied inside `agent.sb` with “Operation not permitted.” A full Vibe run could not be verified here because `OPENROUTER_API_KEY` is not set in this workspace's environment; no provider request was made.
