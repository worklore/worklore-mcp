# Answer: codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed`, run as `./run.sh <task> codex-sandboxed [rep]`.
  - It runs the same `codex exec` call as the `codex` lane (same flags, same `--json` stream, same `-C` workdir), wrapped in `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, the same way the `kimi` lane is wrapped.
  - Codex gets an empty scratch `HOME` and `CODEX_HOME` (`/tmp/chome-*`). The real `~/.codex` is not visible, so its `auth.json` and MCP server config are not loaded.
  - Auth comes from `CODEX_API_KEY` in the environment. The lane exits 2 with a message if the key is unset.
  - `-o` writes into a scratch folder in `/tmp`, which the profile allows. After `sandbox-exec` returns, the lane copies `final.txt` into the run folder and deletes the scratch folder.
  - If the run exits 0 but `final.txt` is missing or empty, the lane marks the run as failed (exit 1).
  - `stdout`/`stderr` still redirect straight into `runs/.../agent.log` and `agent.err`. The outer shell opens them before the sandbox starts.
- **`README.md`**: added the new lane to the lane list.
- **`sandbox/agent.sb`**: not changed. The new lane uses the profile as it is.
- **`codex` and `kimi` lanes**: not changed.

## Colleague's note: what applied

- **Applied: the scratch-folder fix.** `-o` must not point into a denied folder. The lane writes it to `/tmp` and copies it out after the sandbox exits.
- **Applied: don't trust the exit code alone.** The lane checks that `final.txt` exists and is non-empty before it reports success.
- **Applied: stdout/stderr redirects stay outside the sandbox.** This was already the case, and I kept it.
- **Applied in principle, not verified in place: the premise.** The note's failure needs the run folder under the real home. In this checkout the repo is at `/private/tmp/h-NMesor`, outside `$HOME`, so `-o` into `runs/` would have been allowed here. The README says the eval Mac keeps the repo at `~/evals/agent-evals`, under `$HOME`. There `-o` into `runs/` would be denied. I checked that the profile denies writes under `$HOME` (below), but I did not run the lane from `~/evals`.
- **Not applied: grepping `agent.err` for "Operation not permitted".** I left this out as a failure signal. The agent's own shell can hit a denied write legitimately, and that shouldn't fail a run whose answer was written. The `final.txt` check covers the `-o` case directly.
- **Not applicable: Mistral Vibe, `--output-dir`, the `check_answer.py` side.** This harness has no Vibe lane. `check_answer.py` already reads `final.txt` for every non-Kimi lane, so I left it alone.

## How I checked it

1. **Syntax:** `bash -n run.sh` passes.
2. **Profile behavior:** under `sandbox/agent.sb` with `-D HOME=$HOME`, a write to `/tmp` succeeds and a write under `$HOME` fails with "Operation not permitted". This is the premise the lane relies on.
3. **Lane mechanics, with a stub `codex` on `PATH`:**
   - A stub that writes its `-o` file and exits 0: `final.txt` is copied into the run folder, `answer.json` has the text, `rc=0`. The stub's probe write under the real home was denied.
   - A stub that exits 0 without writing `-o`: `rc=1` with the "no final.txt" message.
   - No `CODEX_API_KEY`: `rc=2`, nothing runs.
4. **Real Codex binary, against a closed port with a dummy key:** the first attempt failed because `CODEX_HOME` must exist. The stub had hidden that, so I added `mkdir "$SH/.codex"`. After the fix, Codex starts, writes its state into the scratch home, and produces no "Operation not permitted" lines. It then fails at the OpenAI auth handshake with a 401.

## What I could not verify

- **No end-to-end smoke run with a real answer.** `CODEX_API_KEY` is not set in this environment, and the `codex` lane here logs in from `~/.codex/auth.json`. The sandboxed lane therefore has never produced a graded answer. The first real run needs `CODEX_API_KEY` set, for example `CODEX_API_KEY=... ./run.sh fizz codex-sandboxed 1`.
- **`OPENAI_BASE_URL` was ignored** by this Codex version. My dummy-key test therefore reached `api.openai.com`, and the 401 came back before any prompt was sent. I did not use a real key for it.

## Differences from the `codex` lane, and trade-offs

- **Auth is an environment variable, not a file.** The profile blocks reads of files under `$HOME`, but the agent's shell still inherits `CODEX_API_KEY` from the environment and could read it or send it over the open network. The sandbox does not protect that key. The lane keeps the real `auth.json` out of reach, but an env-var key is still visible to the agent.
- **Codex runs with its defaults.** The real `~/.codex/config.toml` pins no model or provider, so the default model applies in both lanes. It also defines MCP servers, which the sandboxed run does not load. That keeps the sandboxed run from reaching anything through MCP, but it is still a difference from the `codex` lane.
- **Codex's install must sit outside `$HOME`.** The profile denies reads under `$HOME`, so a Codex or Node install under it (for example, via nvm) would fail to start inside the sandbox. Here `codex` is at `/opt/homebrew/bin/codex`, and the real-binary test above shows it starts. On the eval Mac this needs checking too.

## Other notes

- `/tmp/chome-UT8cZY` was there before I started (timestamp 14:58, before this session's changes). I did not touch it.
- I did not commit anything. `run.sh`, `README.md`, and the new `ANSWER.md` are changed in the working tree.
