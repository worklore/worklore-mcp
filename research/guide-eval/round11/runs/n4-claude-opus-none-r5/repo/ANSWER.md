# codex-sandboxed lane

## What changed
- `run.sh`: new lane `codex-sandboxed` (`./run.sh <task> codex-sandboxed [rep]`), function `codex_sandboxed_run`.
  It runs the same `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o "$R/final.txt" "$P"`
  as the `codex` lane, but the way `kimi_run` does it:
  - makes an empty scratch HOME (`/tmp/chome-XXXXXX`), exports it as `HOME`, and deletes it afterwards;
  - also sets `CODEX_HOME=$SH/.codex`, so Codex keeps its sessions/sqlite state in the scratch home and never uses the real `~/.codex`;
  - wraps the run in `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, so the agent's shell (and Codex itself) can't read or write anything under the real home.
- `sandbox/agent.sb` is **unchanged**. Codex needs nothing from the home folder: the binary is in `/opt/homebrew`, and it logs in with `CODEX_API_KEY` from the environment (per the README). So the only hole the profile opens is still `~/.kimi-code`, which belongs to the kimi lane.
- `--dangerously-bypass-approvals-and-sandbox` stays on. Codex's own Seatbelt sandbox can't run nested inside `sandbox-exec`; `agent.sb` is now the fence.
- `README.md`: added the lane to the list.
- `check_answer.py` needed no change. It reads `final.txt` for any lane that doesn't start with `kimi`, so this lane is graded the same way as `codex`.

## Behaviour difference vs. `codex`
With a scratch `CODEX_HOME`, the real `~/.codex/config.toml` isn't loaded. That config sets no model, but it does turn on an MCP server (`pencil`, which lives in the home folder anyway) and the `github`/`posthog` plugins. This lane runs without them; the plain `codex` lane still has them.

## How it was checked (local only, no agent run)
- `bash -n run.sh` passes. Unknown lanes still exit 2.
- I ran a shell under the same `sandbox-exec -D HOME=… -f sandbox/agent.sb` setup with a scratch HOME/CODEX_HOME:
  reading `~/.codex/config.toml` was denied, writing to `~` was denied (no file was created), writing to the scratch HOME and creating `CODEX_HOME` worked, and `codex --version` and `codex exec --help` ran fine inside the sandbox.
- I did **not** run a real Codex task. That would send the prompt to OpenAI, and `CODEX_API_KEY` isn't set in this shell. The first real run is `./run.sh fizz codex-sandboxed` with the key exported.
