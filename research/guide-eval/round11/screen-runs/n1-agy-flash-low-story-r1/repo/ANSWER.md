# Cause of Failure and Resolution

## Cause of the Failure
When Mistral Vibe CLI starts up, even if configured to use an alternative provider like OpenRouter, it checks for a Mistral API key (`MISTRAL_API_KEY`). Because `run-vibe.sh` runs Vibe inside an isolated environment via `env -i`, `MISTRAL_API_KEY` was unset. When unset in the environment or `.env` files, Vibe attempts to read credentials from the macOS Keychain by invoking `/usr/bin/security find-generic-password -s ai.mistral.vibe ...`.

However, the sandbox profile `agent.sb` explicitly denies execution of `/usr/bin/security` (`(deny process-exec ... (literal "/usr/bin/security") ...)`). Consequently, the attempt to execute `/usr/bin/security` was denied with `Operation not permitted`, causing Vibe to crash immediately on startup with exit code 2 and write:
```
Reading API keys from the macOS Keychain (set them as environment variables to skip this)
Error: [Errno 1] Operation not permitted: '/usr/bin/security'
```

## Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Identification of root cause**: Vibe queries macOS Keychain via `/usr/bin/security` at startup when `MISTRAL_API_KEY` is not present in the environment, even when using a non-Mistral provider (OpenRouter).
- **Sandbox denial**: The sandbox profile `agent.sb` intentionally denies execution of `/usr/bin/security`, which caused the crash.
- **The fix**: Passing a dummy/non-empty `MISTRAL_API_KEY` (e.g. `MISTRAL_API_KEY="unused"`) directly on the `env -i` execution line in `run-vibe.sh` bypasses the Keychain lookup without modifying or loosening `agent.sb`.
- **Verification steps**: Keeping `agent.sb` unchanged, verifying that the Keychain access error disappears, confirming that `/usr/bin/security` remains blocked under `agent.sb`, and confirming that Vibe initializes and reaches the provider.

### Parts ignored / not used:
- Creating a `.env` in `VIBE_HOME`: Unnecessary since setting the environment variable in `env -i` within `run-vibe.sh` cleanly addresses the issue.
- `VIBE_TEST_DISABLE_KEYRING=1`: Ignored as an undocumented internal/test switch as noted by the colleague.
- Loosening the sandbox: Ignored, as `/usr/bin/security` must remain denied to protect local credentials.

## Fix Implemented
In `run-vibe.sh`, `MISTRAL_API_KEY="unused"` was added to the `env -i` environment variables:
```bash
( cd "$W" && env -i PATH="$PATH" TERM="${TERM:-dumb}" LANG="${LANG:-en_US.UTF-8}" HOME="$SH" VIBE_HOME="$VH" \
    OPENROUTER_API_KEY="$OPENROUTER_API_KEY" MISTRAL_API_KEY="unused" \
    sandbox-exec -D HOME="$REAL" -f "$D/agent.sb" \
    ...
```
