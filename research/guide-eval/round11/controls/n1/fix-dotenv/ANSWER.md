Cause: with no MISTRAL_API_KEY in its environment, Vibe looks for its Mistral key in the macOS Keychain by running
/usr/bin/security, even though the provider is OpenRouter. agent.sb denies /usr/bin/security, so Vibe stops with
exit 2. Fix: pass MISTRAL_API_KEY=unused (any value) on the env -i line; the sandbox stays as it is.
