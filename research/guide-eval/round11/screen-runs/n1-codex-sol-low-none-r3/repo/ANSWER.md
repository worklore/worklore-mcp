# Cause

Vibe 3.1.0 checks for `MISTRAL_API_KEY` during startup even when the configured model uses OpenRouter. The launcher's `env -i` removed that variable, so Vibe tried to read API keys from the macOS Keychain via `/usr/bin/security`. `agent.sb` correctly blocks that command, causing the immediate exit 2 before any run or export.

The launcher now supplies an inert `MISTRAL_API_KEY` placeholder to prevent the Keychain lookup. The OpenRouter provider still uses `OPENROUTER_API_KEY`; the real key is not copied to the Mistral variable. The sandbox's Keychain denial remains in place.
