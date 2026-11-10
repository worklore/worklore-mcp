# Answer: `codex-sandboxed` lane

## What I did

`run.sh` has a new lane, `codex-sandboxed`. It runs the same `codex exec` call as the `codex` lane, but the whole Codex process runs under `sandbox/agent.sb` with the same pattern as `kimi_run`:

- `HOME` is a fresh scratch folder in `/tmp`, and `sandbox-exec -D HOME="$REAL"` denies reads and writes under the real home.
- `CODEX_HOME` points at `$SH/.codex`, which holds copies of `~/.codex/config.toml` and `~/.codex/auth.json`. The sandbox blocks the real `~/.codex`, and Codex needs its login and config.
- `-o` writes to a scratch folder in `/tmp` (`$CS/final.txt`). After `sandbox-exec` returns, the lane copies it into `runs/<task>-codex-sandboxed-r<rep>/final.txt`, then deletes both scratch folders.
- stdout and stderr go straight into the run folder from the outer shell, as in the other lanes.
- The lane prints a warning if `final.txt` is missing or empty, or if `agent.err` contains `Operation not permitted`.

Files changed: `run.sh` (new lane, header comment), `README.md` (lane list, and a corrected paragraph about where Codex reads its login from). `sandbox/agent.sb` and the `codex` and `kimi` lanes are unchanged.

Usage: `./run.sh fizz codex-sandboxed 1`

## Which parts of the colleague's note applied

- **Applied: the `-o` write into a denied folder.** The README says the repo lives at `~/evals/agent-evals` on the eval Mac, so the run folders sit under the real home there. I checked the fence directly: under the profile, a write to a path under the real home fails with `Operation not permitted`, while writes to `/tmp` and to the repo work when the repo is outside home (as in this checkout). So `-o` goes to `/tmp` and is copied out after the sandbox exits.
- **Applied: keep stdout and stderr redirects outside the sandbox.** This was already the pattern in `kimi_run`.
- **Applied: don't trust the exit code alone.** The lane checks for a non-empty `final.txt` and greps `agent.err` for `Operation not permitted`.
- **Not applied:** the Mistral Vibe parts (`--output-dir`, that tool, its run layout) and the sample run-folder grep, since this repo has no Vibe lane. The note's claim that Codex exits 0 after a failed `-o` write is from the note; I did not reproduce it with a live Codex run.

## Verification

No live Codex run. A real run sends the task to OpenAI and spends tokens, so I only ran offline checks:

1. **The fence, with the same profile and arguments as the lane:**
   - `cat` of the real `~/.codex/auth.json` from inside the sandbox: `Operation not permitted`.
   - Writing under the real home: `Operation not permitted`.
   - Writing to the repo and to `/tmp`: allowed.
2. **`codex --version` under the profile** with the scratch `HOME` and `CODEX_HOME`: prints `codex-cli 0.160.0`. The binary is a Node script; `node` and `codex` both run from `/opt/homebrew`, outside home, so the profile doesn't block them.
3. **`codex mcp list` under the profile:** runs and reads the copied config.
4. **The lane end to end with a stub `codex` on `PATH`:** the stub wrote `-o`, and the lane copied it to `final.txt`. `meta.json` has `exit_code: 0`, and `answer.json` read `source: final.txt`. Inside the stub, the real `auth.json` read was denied and the real-home write was denied. Scratch folders were removed afterwards.

The stub's probe write produced the `Operation not permitted` line in `agent.err`, so the warning fired as intended. That was the probe, not a lane failure.

Test artifacts (the stub, the `fizz-codex-sandboxed-r1` run folder, my scratch dirs) are removed. Scratch `/tmp/chome-*` folders from 14:58 and 15:37 today predate this work and are not mine, so I left them alone.

## Differences from the `codex` lane

- **MCP server under the real home.** `config.toml` has a `pencil` MCP server whose binary is at `/Users/valentinakoniukhova/.pencil/...`. The sandbox blocks that binary, so the server should fail to start in this lane. `codex mcp list` only reads config, so I did not confirm the runtime failure. The lane leaves the config unchanged, so the run matches the `codex` lane's config; the cost is that the MCP server doesn't run.
- **Codex's state files** (sessions, sqlite) go to the scratch `CODEX_HOME`, which is deleted at the end of the run. The `codex` lane writes them to `~/.codex`. They are not in the run folder.
- **The login is still readable by the agent's shell.** Codex needs its credential, and the shell inherits the same environment. The sandbox protects the real home's files, not the credential the model call needs. `kimi`'s `~/.kimi-code` has the same exposure.
- **README correction.** The old README said Codex needs nothing from the home folder. That doesn't match `auth.json`, which holds ChatGPT tokens, so I rewrote the paragraph. I did not confirm whether the `codex` lane uses `auth.json` or `CODEX_API_KEY` first.

## Not done

- Nothing committed or pushed.
- No live run. To check it for real: `./run.sh fizz codex-sandboxed 1`, then confirm `runs/fizz-codex-sandboxed-r1/final.txt` is non-empty and `agent.err` has no `Operation not permitted`.
