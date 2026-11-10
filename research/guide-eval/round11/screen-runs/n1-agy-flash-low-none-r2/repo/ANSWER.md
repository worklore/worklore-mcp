# Cause of Headless Vibe Failure

## Why the Script Failed

When Mistral Vibe (`vibe-rs` and its backend services) starts up, it attempts to resolve credentials for configured and default providers. Specifically, unless a default `MISTRAL_API_KEY` is present in the environment, Vibe queries the macOS Keychain by invoking `/usr/bin/security find-generic-password -s ai.mistral.vibe -a MISTRAL_API_KEY -w`.

However:
1. `run-vibe.sh` runs `vibe` inside `agent.sb` using `sandbox-exec`.
2. `agent.sb` strictly denies process execution of `/usr/bin/security`:
   ```scheme
   (deny process-exec (literal "/bin/launchctl") (literal "/usr/bin/security") (literal "/usr/bin/osascript"))
   ```
3. Because `run-vibe.sh` used `env -i` with an allowlist containing only `PATH`, `TERM`, `LANG`, `HOME`, `VIBE_HOME`, and `OPENROUTER_API_KEY`, no Mistral key or keyring disable flag was passed to the process.
4. When `vibe` attempted to execute `/usr/bin/security` to check the Keychain, macOS denied execution with `[Errno 1] Operation not permitted: '/usr/bin/security'`, leading to an immediate unhandled fatal crash (exit code 2) before initiating any model sessions.

## The Fix

`VIBE_TEST_DISABLE_KEYRING=1` is Vibe's built-in mechanism to disable accessing the system OS keyring / macOS Keychain. 

In [run-vibe.sh](file:///tmp/h-FGcl0r/run-vibe.sh#L14-L18), `VIBE_TEST_DISABLE_KEYRING="1"` was added to the `env -i` environment passed to `vibe`:
```bash
( cd "$W" && env -i PATH="$PATH" TERM="${TERM:-dumb}" LANG="${LANG:-en_US.UTF-8}" HOME="$SH" VIBE_HOME="$VH" \
    OPENROUTER_API_KEY="$OPENROUTER_API_KEY" VIBE_TEST_DISABLE_KEYRING="1" \
    sandbox-exec -D HOME="$REAL" -f "$D/agent.sb" \
    "$VIBE" -p "$PROMPT" --model devstral --auto-approve --trust --output streaming --output-dir "$VH/out" \
      --max-price 1.5 --time-limit 1200 < /dev/null > "$D/logs/last-run.out" 2> "$D/logs/last-run.err" )
```

This prevents `vibe` from attempting to spawn `/usr/bin/security`, keeping the run completely isolated from the Keychain while allowing headless runs on OpenRouter to proceed and generate session exports normally.
