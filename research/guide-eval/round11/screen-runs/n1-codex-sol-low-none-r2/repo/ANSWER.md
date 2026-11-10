# Cause and fix

Vibe 3.1.0 failed during session setup, before it sent a prompt. Its automatic utility-model selection looked for a built-in Mistral model. Because `MISTRAL_API_KEY` was absent from the script's `env -i` environment, Vibe tried to read it from the macOS Keychain by running `/usr/bin/security`. The sandbox correctly denies that command, producing exit 2.

Even after selecting the OpenRouter model for utility tasks, Vibe's built-in web-search availability check still resolves `MISTRAL_API_KEY` before disabled tools are filtered. That was a second route to the same failure.

The config now routes both utility tasks to `devstral` and disables the Mistral web-search tool. The launcher supplies a non-secret `MISTRAL_API_KEY=unused` placeholder solely to satisfy Vibe's startup availability check; the real OpenRouter key remains the only usable provider credential. The sandbox's Keychain and home-directory restrictions remain in place.

Verification: an offline probe with a dummy OpenRouter key and network access denied advanced past session setup and ran until its five-second deadline (exit 3), with no Keychain error. No external service was contacted.
