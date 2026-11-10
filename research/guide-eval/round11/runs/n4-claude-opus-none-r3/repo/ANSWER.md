# codex-sandboxed lane

`./run.sh <task> codex-sandboxed [rep]` runs the same `codex exec` command as the `codex` lane (same flags, prompt, timeout, `--json` stream to `agent.log`, last message to `final.txt`), but wrapped the way `kimi` is:

- an empty scratch HOME (`/tmp/chome-XXXXXX`, deleted afterwards), with `CODEX_HOME` pointing at a scratch `.codex` inside it;
- `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, so the agent's shell can't read or write anything under the real home.

## Changes

- **run.sh**: new `codex_sandboxed_run` function and a `codex-sandboxed)` case; lane added to the usage comment.
- **sandbox/agent.sb**: the profile used to open `~/.kimi-code` for every lane that used it. Reused as it was, that would have let Codex's shell read Kimi's install, credentials and sessions, which are in the real home. The opened folder is now a parameter, `-D AGENT_DIR=<dir>`:
  - `kimi` passes `$HOME/.kimi-code`, so it gets exactly the access it had before.
  - `codex-sandboxed` passes its scratch HOME, which is outside the real home.
- **README.md**: lane documented.

## Details worth knowing

- **Nothing in the real home is opened for Codex, not even `~/.codex`.** Per the README, Codex logs in with `CODEX_API_KEY` from the environment, so it doesn't need `auth.json` and starts each run from an empty `CODEX_HOME`. This also means your `~/.codex/config.toml` (model, profiles, MCP servers) is **not** used here. If the plain `codex` lane depends on settings in it, the two lanes won't be exactly the same. To fix that, put a copy of the config in the scratch `.codex` or pass the settings with `-c`.
- **Where `final.txt` gets written.** `codex -o` is written by Codex from inside the sandbox. On the eval Mac the repo is in `~/evals/agent-evals`, which is under the real home, so writing directly to `runs/...` would be blocked. The lane writes `final.txt` into the scratch HOME and copies it to the run folder afterwards. `agent.log` and `agent.err` are fine as they are, because the shell opens those redirects outside the sandbox.
- **Codex's built-in sandbox is still turned off** (`--dangerously-bypass-approvals-and-sandbox`), as in the `codex` lane. Codex's own sandbox is Seatbelt too, and `sandbox-exec` can't run inside another sandbox. `agent.sb` takes its place.
- **Network access is open**, same as in `kimi`.

## Verification

- `bash -n run.sh` passes.
- I ran the lane's exact sandbox setup with a probe script in place of the agent.
  - With the `codex-sandboxed` parameters:
    - blocked: reading `~/.codex/auth.json`, listing `~/.codex`, reading `~/.kimi-code`, and writing a file in `~`;
    - allowed: writing to the scratch HOME and to the work folder, and running `codex --version` and `timeout`.
  - With the `kimi` parameters, the only change is that reading `~/.kimi-code` is allowed, which is the same as before the change.
- **Not done:** a real end-to-end run. `CODEX_API_KEY` isn't set on this machine, and a run would send the prompt to OpenAI. The first real run is `./run.sh fizz codex-sandboxed`. Check that `runs/fizz-codex-sandboxed-r1/answer.json` has a non-empty `final` and that `agent.err` has no `Operation not permitted`.
