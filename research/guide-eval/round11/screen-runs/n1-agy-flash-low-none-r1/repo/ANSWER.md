# Cause of Failure and Resolution

## Cause of Failure

1. `run-vibe.sh` executes Vibe inside a clean environment using `env -i`, passing only select environment variables (`PATH`, `TERM`, `LANG`, `HOME`, `VIBE_HOME`, `OPENROUTER_API_KEY`).
2. Even when `OPENROUTER_API_KEY` is provided, Vibe's backend startup checks the macOS Keychain for stored credentials via `/usr/bin/security`.
3. The macOS sandbox profile `agent.sb` specifically restricts Keychain access and denies execution of security tools with `(deny process-exec (literal "/bin/launchctl") (literal "/usr/bin/security") (literal "/usr/bin/osascript"))`.
4. When Vibe attempts to execute `/usr/bin/security` to inspect the Keychain, the sandbox blocks execution with `[Errno 1] Operation not permitted: '/usr/bin/security'`, leading to an immediate unhandled crash with exit code 2.

## Fix

Vibe provides an environment variable `VIBE_TEST_DISABLE_KEYRING=1` (supported in both the Python keyring integration and the Rust core) to completely disable querying the OS keyring / macOS Keychain.

In [run-vibe.sh](file:///tmp/h-uZhMeF/run-vibe.sh), `VIBE_TEST_DISABLE_KEYRING=1` was added to the `env -i` environment passed to `sandbox-exec`. This prevents Vibe from invoking `/usr/bin/security` inside the sandbox, allowing it to authenticate purely via `OPENROUTER_API_KEY` without crashing.
