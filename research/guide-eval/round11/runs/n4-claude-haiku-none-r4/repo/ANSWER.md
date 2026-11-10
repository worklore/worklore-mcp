# codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed`, implemented by `codex_sandboxed_run()`.
  - It runs the same `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json` command as the `codex` lane, with the same prompt and timeout.
  - The whole codex process tree runs under `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, the same profile the `kimi` lane uses.
  - `HOME` and `CODEX_HOME` point at a fresh scratch directory under `/tmp/chome-*`, which is removed afterwards.
  - Codex writes its last message (`-o`) into that scratch directory, because the sandbox would block a write into the real home if the run folder were under it. The file is moved to `runs/<task>-codex-sandboxed-r<rep>/final.txt` after the sandbox exits.
  - The header comment and the `case` dispatch list the new lane.
- **`README.md`**: one bullet describing the lane.
- **`sandbox/agent.sb`**: unchanged. Codex is installed under `/opt/homebrew`, outside the home folder, so the profile needs nothing new. It opens no part of `~/.codex`, on purpose.

## Verification

- `bash -n run.sh` passes.
- **Sandbox probe**, run through `sandbox-exec` with the real profile:
  - reading `~/.gitconfig` is denied;
  - creating a file in the real home is denied;
  - writing to the scratch HOME and to `/tmp` is allowed.
- **Lane plumbing**: I ran `./run.sh fizz codex-sandboxed 1` with a stub `codex` first on PATH. The stub recorded `HOME` and `CODEX_HOME` pointing at the scratch dir, failed to read the real `~/.gitconfig`, and wrote the `-o` file. `final.txt`, `agent.log`, `agent.err` and `meta.json` all landed in the run folder, and `check_answer.py` read the answer. The stub, the probe directories and the test run folder were deleted afterwards.

## Not verified / caveats

- **No real Codex run.** A real run sends the task to OpenAI, and you asked me not to submit anything to external services. The lane has not been exercised against the real `codex` binary.
- **Authentication is the main risk.** On this machine `CODEX_API_KEY` is not set, and Codex logs in from `~/.codex/auth.json`. The sandbox blocks that file, so **the lane will fail to authenticate unless `CODEX_API_KEY` is exported** when `run.sh` is called. This also means the README's older claim, that Codex "needs nothing from the home folder", holds only with an API key. I did not try to pass the auth file in, because the agent's shell would then be able to read it.
- **Config is not carried over.** `CODEX_HOME` is empty, so `~/.codex/config.toml` (MCP servers, project trust levels) does not apply inside the sandboxed lane. I found no top-level `model` setting there, so the default model should match, but the run is not byte-for-byte the `codex` lane.
- **Leftover directories I did not create.** `/tmp` contains `chome-K5ToQJ`, `chome-TURZsd` and `chome-UT8cZY`, dated earlier today. I left them alone.
- **Nothing committed.** Changes are in the working tree only.
