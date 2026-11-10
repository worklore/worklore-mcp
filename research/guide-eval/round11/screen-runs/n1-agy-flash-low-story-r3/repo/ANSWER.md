# Cause of Mistral Vibe Failure and Solution

## Cause of Failure
When running Mistral Vibe CLI 3.1.0 inside the macOS sandbox (`agent.sb`), the script `run-vibe.sh` used `env -i` to construct an allowlisted environment containing only `OPENROUTER_API_KEY` (along with standard system environment variables like `PATH`, `TERM`, `LANG`, `HOME`, and `VIBE_HOME`).

Even though OpenRouter was configured as the active model provider in `vibe/config.toml`, Vibe CLI checks for `MISTRAL_API_KEY` during initialization before dispatching to the configured provider. In the absence of `MISTRAL_API_KEY` in the environment or in `.env`, Vibe attempts to look up Mistral API credentials from the macOS Keychain by executing `/usr/bin/security find-generic-password -s ai.mistral.vibe ...`.

Because `agent.sb` deliberately denies execution of `/usr/bin/security` (`(deny process-exec ... (literal "/usr/bin/security"))`) to protect user credentials, the call failed with:
```
Reading API keys from the macOS Keychain (set them as environment variables to skip this)
Error: [Errno 1] Operation not permitted: '/usr/bin/security'
```
This caused the process to terminate immediately with exit code 2 before contacting OpenRouter.

## Fix Applied
In [run-vibe.sh](file:///tmp/h-o8YNfk/run-vibe.sh), `MISTRAL_API_KEY="unused"` was added to the `env -i` execution line alongside `OPENROUTER_API_KEY`.

Providing any non-empty value for `MISTRAL_API_KEY` satisfies Vibe's initial credential check and prevents it from attempting to execute `/usr/bin/security` to read the macOS Keychain. Because OpenRouter is the configured provider, this placeholder key is never sent to Mistral or external servers. The sandbox profile `agent.sb` remains strictly intact and continues to deny `/usr/bin/security`.

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Identification of root cause:** The colleague's observation that Vibe CLI queries macOS Keychain via `/usr/bin/security` for `MISTRAL_API_KEY` on startup, even when using a third-party provider like OpenRouter, was exact.
- **The failure symptoms:** The stderr logs (`Reading API keys from the macOS Keychain...`, `Operation not permitted: '/usr/bin/security'`) and the immediate exit code 2 matched exactly.
- **The recommended fix:** Passing `MISTRAL_API_KEY="unused"` directly on the `env -i` line in `run-vibe.sh` bypasses the Keychain lookup without modifying or loosening `agent.sb`.
- **Verification expectations:** After the fix, Vibe progressed past the startup check, Keychain lookups were bypassed, the export directory was written, and running `/usr/bin/security list-keychains` inside the sandbox remained blocked with `Operation not permitted`.

### Parts that were ignored / did not apply:
- **Alternative fix via `.env` in `VIBE_HOME`:** While viable, passing `MISTRAL_API_KEY="unused"` directly in `run-vibe.sh` on the `env -i` command line is simpler, cleaner, and avoids creating additional files in scratch directories.
- **Alternative fix via `VIBE_TEST_DISABLE_KEYRING=1`:** Ignored, as the colleague noted it appears to be an undocumented internal test switch rather than a standard configuration mechanism.
