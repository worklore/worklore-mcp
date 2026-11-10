# Why every run exits in about a second

**Cause:** Vibe's Rust client (`vibe-rs`, bundled in the Mistral Vibe 3.1.0 wheel) reads the macOS Keychain at startup,
and `agent.sb` denies `/usr/bin/security`.

1. `run-vibe.sh` starts `vibe` inside `sandbox-exec -f agent.sb`.
2. Before any API call, `vibe-rs` runs `/usr/bin/security find-generic-password -s ai.mistral.vibe -a MISTRAL_API_KEY -w`
   to print "Reading API keys from the macOS Keychain". The `MISTRAL_API_KEY` lookup happens even though the config
   uses only the OpenRouter provider, and setting `OPENROUTER_API_KEY` does not skip it.
3. `agent.sb` has `(deny process-exec ... (literal "/usr/bin/security") ...)`, so the exec fails with
   `Error: [Errno 1] Operation not permitted: '/usr/bin/security'`. The run exits with 2 and never reaches OpenRouter.

This is the sandbox doing its job. The bug is that the run never tells Vibe the Keychain is off limits.

**Evidence:**
- `logs/last-run.err` contains exactly that error.
- Reproduced with a dummy key: exit 2, same error, in the sandbox.
- Unsandboxed, the same command gets past the Keychain step and reaches OpenRouter.
- `VIBE_TEST_DISABLE_KEYRING=1` is the switch Vibe provides for this. Inside the sandbox with it set, the run gets
  through to the OpenRouter request and fails only with the dummy key's `Invalid API key`.

**Fix (in `run-vibe.sh`):** pass `VIBE_TEST_DISABLE_KEYRING=1` in the `env -i` list. The API key still comes from the
environment, which is what the script already does. Nothing is read from the Keychain, which makes the sandbox's
intent stricter, not looser. `agent.sb` is unchanged.

**Not verified:** I did not run a real request, because the real `OPENROUTER_API_KEY` is not in this environment. The
dummy-key runs show that startup now gets past the Keychain and reaches OpenRouter. Whether a real key then completes a
task is unverified. Also, `VIBE_TEST_DISABLE_KEYRING` is a test-named variable. It is read by the Python keyring module
and referenced by `vibe-rs`, but Vibe does not document it as a supported switch, so it may change in a future release.
