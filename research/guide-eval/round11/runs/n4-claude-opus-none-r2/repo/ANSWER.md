# codex-sandboxed lane

## What changed

`run.sh` has a new lane, `codex-sandboxed` (`./run.sh <task> codex-sandboxed [rep]`), handled by `codex_sandboxed_run`:

- **Same Codex run as `codex`**: the same `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o … "$P"`, the same timeout, and the same `agent.log`/`agent.err` redirects.
- **Fenced the way `kimi` is**: `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb` wraps the whole Codex process tree, so the agent's shell commands run inside it too. HOME is an empty scratch folder (`/tmp/chome-XXXXXX`) that gets deleted after the run.
- **`CODEX_HOME=$SCRATCH/.codex`**: Codex keeps its sessions and state in the scratch HOME and never touches `~/.codex`. It logs in with `CODEX_API_KEY` from the environment (as the README says), so `agent.sb` didn't need to change. Unlike `~/.kimi-code` for Kimi, nothing under the real home is opened for Codex.
- **`final.txt`**: the README says the harness lives in `~/evals/agent-evals`, so the run folder is under the real home. The sandboxed Codex can't write there, so `-o` would have failed and the graders would get no answer. Codex now writes `-o` into the scratch folder, and the file is copied to `runs/…/final.txt` after the run. `agent.log` and `agent.err` are fine as they are: the shell opens those redirects outside the sandbox, before `sandbox-exec` starts.
- Codex's own `--dangerously-bypass-approvals-and-sandbox` stays on, as in the `codex` lane. Seatbelt sandboxes can't be nested, so Codex's built-in sandbox wouldn't work inside `agent.sb` anyway. `agent.sb` is the fence.
- `check_answer.py` needs no change: a lane that doesn't start with `kimi` reads `final.txt`.
- I updated the usage comment in `run.sh` and the lane list in `README.md`.

## How I checked it

- `bash -n run.sh` passes.
- Under the exact profile and environment the lane uses, I ran a local smoke test with no API calls:
  - `codex --version` (0.160.0) and `codex exec --help` run fine inside the sandbox.
  - Reading `~/.codex/auth.json` is denied.
  - Creating a file in the real home is denied.
  - Writing into the scratch `CODEX_HOME` works.
  - `HOME` points to the scratch folder.

**Not done:** I didn't do a real `./run.sh fizz codex-sandboxed` run, because it would send the task to OpenAI's API and the ground rules rule out external services. Do one before relying on the lane. If Codex fails at startup, look in `agent.err` for a denied path under the real home.

## Limits

- The fence covers the filesystem, not the network: like `kimi`, network access stays open.
- `CODEX_API_KEY` is in the agent's environment, so its shell can read it, just as in the `codex` lane.
- In the profile, "home" means `$HOME` only. Paths outside it, like `/tmp` and `/opt/homebrew`, can still be read, also as in the `kimi` lane.
