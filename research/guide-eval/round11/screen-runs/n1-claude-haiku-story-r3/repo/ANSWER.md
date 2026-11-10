# Why run-vibe.sh exited at once, and the fix

## Cause

At startup Vibe's front end (`vibe-rs`, bundled in the pipx venv that `~/.local/bin/vibe` points to) reads
`MISTRAL_API_KEY` from the macOS Keychain whenever that variable is unset. It does this even though the active
provider is OpenRouter. It runs `/usr/bin/security find-generic-password -s ai.mistral.vibe ...`. `agent.sb`
denies that exec on purpose, so the call fails with `Operation not permitted`. Vibe does not handle that error
and exits with status 2 after about two seconds, before any model call.

Evidence:

- Reproduced with a dummy `OPENROUTER_API_KEY`: stderr has exactly the two lines from the original log, and the
  run exits 2.
- The Keychain call is in the Rust binary (`vibe/_bin/vibe-rs`). Its strings contain `VIBE_TEST_DISABLE_KEYRING`,
  `/usr/bin/security`, `find-generic-password -s ... ai.mistral.vibe`, `MISTRAL_API_KEY`, and "macOS Keychain".
  The message "Reading API keys from the macOS Keychain" is printed there, not by the Python package.
- A config-level fix does not work. The default `mistral` provider is always present (providers union-merge by
  name), and overriding its `api_key_env_var` still triggers the Keychain read.

## Fix

`run-vibe.sh` now passes `VIBE_TEST_DISABLE_KEYRING=1` on the `env -i` line. Both the Python keyring code
(`vibe/utils/keyring.py`, `_is_keyring_disabled`) and the Rust front end read this switch, so Vibe makes no
Keychain reads at all. The OpenRouter key still comes from the environment, which Vibe checks first. The sandbox
is unchanged.

I also fixed a launcher bug I found while testing. On a second run, `cp -R` nested the new export under the
existing `logs/last-run-export/out/`, so `logs/last-run-export/export.json` kept showing the first run. The
launcher now removes the old export folder before copying.

Why not the sentinel `MISTRAL_API_KEY=unused`: it also stops the startup failure (tested), but it is a false
credential. `WebSearch.is_available()` treats any non-empty `MISTRAL_API_KEY` as usable, so the web-search tool
would be offered and would send `unused` as a bearer token to Mistral's API. The switch avoids that. Use the
sentinel only if the switch stops working in a later Vibe release. An empty value does not work either, because
an empty env value is treated as unset and the Keychain is still read.

## Verification

With the real `run-vibe.sh`, the unchanged `agent.sb`, and a dummy OpenRouter key:

- The Keychain line is gone. Stderr is `Error: Invalid API key (from env var OPENROUTER_API_KEY). Please check
  your API key and try again.` Vibe reached OpenRouter and failed there, as expected for a dummy key.
- `export.json` is written with `outcome: config_error`, `exit_code: 1`, and that same message.
- Inside the same sandbox profile, `/usr/bin/security list-keychains` fails:
  `sandbox-exec: execvp() of '/usr/bin/security' failed: Operation not permitted` (exit 71).

I did not test with a real OpenRouter key, so the successful model call is not verified.

## Colleague's note: what applied

Applied:

- The cause: a Keychain read for `MISTRAL_API_KEY` through `/usr/bin/security`, denied by the sandbox, exit 2.
- Keep the sandbox and keep `/usr/bin/security` denied.
- The variable has to be on the `env -i` line.
- The expected verification results (Keychain line gone, failure at the provider with the
  "Invalid API key (from env var OPENROUTER_API_KEY)" message, `security list-keychains` still denied).
- Startup takes about two seconds, which matches "within a second or two".

Not applied, or contradicted by what I found:

- The fix itself. The note recommends `MISTRAL_API_KEY=unused`. I chose `VIBE_TEST_DISABLE_KEYRING=1` because the
  sentinel reaches Mistral through `web_search`, as explained above.
- "Vibe never sends it anywhere": not supported by the code. See the web-search point above.
- "It wrote no export": false. Vibe writes `export.json` with `infrastructure_failure` on this failure.
- "It looks like a test switch, so don't rely on it": the switch is read by production code in both the Python
  and Rust parts. It is undocumented, though, so it could be removed in a later release. If that happens, the run
  fails loudly with the same Keychain error rather than silently, and the sentinel above is the fallback.
- The key lookup order (environment, then `~/.vibe/.env`, then the keyring): the `.env` part comes from the
  installed package docs (METADATA). That `VIBE_HOME/.env` alternative is not tested here.

## Other notes

- `logs/last-run.out` and `logs/last-run.err` now hold the output of the verification run (dummy key), and
  `logs/last-run-export/` is new output from that run. Nothing is committed.
- Scratch folders I created during testing were removed.
