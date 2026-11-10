# Root Cause and Fix

## Cause of Failure
Even though the active model is configured to use OpenRouter (`provider = "openrouter"` via `OPENROUTER_API_KEY`), Mistral Vibe CLI attempts to resolve its default `MISTRAL_API_KEY` at startup before anything else.
Because `run-vibe.sh` executes Vibe via `env -i` with an allowlist that did not pass `MISTRAL_API_KEY`, Vibe fell back to looking for keys in the macOS Keychain by running `/usr/bin/security find-generic-password -s ai.mistral.vibe ...`.
However, the sandbox profile (`agent.sb`) explicitly denies `/usr/bin/security` (`(deny process-exec ... (literal "/usr/bin/security"))`) to protect user credentials. When `/usr/bin/security` was invoked, the sandbox denied execution (`Operation not permitted`), causing Vibe to terminate immediately with exit code 2.

## Applied Fix
In `run-vibe.sh`, `MISTRAL_API_KEY=unused` was added to the `env -i` environment passed to Vibe alongside `OPENROUTER_API_KEY`:

```bash
( cd "$W" && env -i PATH="$PATH" TERM="${TERM:-dumb}" LANG="${LANG:-en_US.UTF-8}" HOME="$SH" VIBE_HOME="$VH" \
    OPENROUTER_API_KEY="$OPENROUTER_API_KEY" MISTRAL_API_KEY=unused \
    sandbox-exec -D HOME="$REAL" -f "$D/agent.sb" \
    ...
```

Providing any non-empty value for `MISTRAL_API_KEY` satisfies Vibe's initial environment check so it does not attempt to query `/usr/bin/security` via macOS Keychain. The sandbox profile (`agent.sb`) remains untouched and strictly enforced.

## Notes on the Colleague's Advice
- **What applied:**
  - The diagnosis that Vibe queries macOS Keychain via `/usr/bin/security` looking for `MISTRAL_API_KEY` even when configured with an alternative provider (OpenRouter).
  - The observation that `/usr/bin/security` is denied by design in `agent.sb` and should remain denied.
  - Passing `MISTRAL_API_KEY=unused` directly on the `env -i` command invocation line in `run-vibe.sh`.
  - The verification methodology: confirming startup proceeds past the Keychain check, exports directories are written, and invalid credentials fail downstream at provider authentication rather than during sandbox keyring execution.
- **What did not apply / was ignored:**
  - Creating or managing a `.env` file in `VIBE_HOME` was unnecessary since passing the variable via `env -i` in `run-vibe.sh` directly addresses the issue cleanly.
  - Setting `VIBE_TEST_DISABLE_KEYRING=1` was ignored as it is an internal test flag.
  - Modifying or loosening `agent.sb` permissions was explicitly avoided.
