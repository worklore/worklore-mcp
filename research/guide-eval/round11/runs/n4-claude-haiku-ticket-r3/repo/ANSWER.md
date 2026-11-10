# ANSWER: codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed` (`codex_sandboxed_run`). It runs the same `codex exec` command as the `codex` lane (same flags, same prompt, same `-C "$W"` workdir, same timeout), under `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, the same way the `kimi` lane does.
  - Codex gets an empty scratch `HOME` and `CODEX_HOME=<scratch>/.codex`, so it never sees `~/.codex`. The `kimi` lane does the same with `HOME` and `KIMI_CODE_HOME`.
  - `-o` points at a scratch folder `mktemp -d /tmp/cout-XXXXXX`, outside every denied path. After `sandbox-exec` returns, `final.txt` is copied into the run folder and both scratch folders are deleted.
  - If Codex exits without writing the last-message file, the lane appends a line to `agent.err`. Codex's exit code alone doesn't prove the file was written.
  - stdout and stderr still redirect straight into the run folder, since the shell opens those before the sandbox starts.
- **`README.md`**: one bullet for the new lane in the lane list.
- **`sandbox/agent.sb`**: unchanged. The `codex` binary lives in `/opt/homebrew`, outside the denied home path, so the profile needed no new rules.
- The `codex` and `kimi` lanes are untouched. `check_answer.py` needed no change, since it reads `final.txt` for any non-kimi lane.

## Checks I ran

- `bash -n run.sh`: syntax OK.
- Profile probe with the real `sandbox-exec` command: reading `~/.codex/config.toml` is denied, writing to `~/.codex` is denied, and writing to the `-o` scratch path and to the scratch `CODEX_HOME` both succeed. `/opt/homebrew/bin/codex --version` runs inside the sandbox (`codex-cli 0.160.0`).
- End-to-end lane run on `fizz` with a stub `codex` on PATH, so no model provider was called. The stub saw `HOME` and `CODEX_HOME` pointing at scratch and could not read the real config. It wrote the `-o` file, which was copied to `final.txt`. `answer.json` came out with the stub text, and the lane's `meta.json` had `exit_code: 0`. I then deleted that test run folder.

## Not verified

- **No live Codex run.** A real run sends the task to OpenAI, and I didn't run one without your go-ahead. So I haven't confirmed that the sandboxed Codex gets through authentication and finishes a task.
- **Authentication is untested.** The README says Codex logs in with `CODEX_API_KEY` and needs nothing from the home folder. `CODEX_API_KEY` is not set in my shell, so I couldn't confirm that. `~/.codex/auth.json` exists, though. If the Codex login is ChatGPT-based and reads `auth.json`, the sandboxed lane will fail to authenticate. I did not copy `auth.json` or open it to the sandbox: the agent's shell could then read the credential, which defeats the sandbox.

## What differs from the `codex` lane

- `~/.codex/config.toml` is not copied into the scratch `CODEX_HOME`, so this lane runs with Codex defaults plus the env key. The real config sets no model or provider (I checked), but it enables the github and posthog plugins and defines two MCP servers, `pencil` (under the home folder) and `posthog`. The sandboxed lane won't have those tools. Copying the file would give the agent's shell a readable copy of the home config, so I left it out. If the comparison needs those tools, that's a decision for you.

## Colleague's note: what applied

- **Applied:** the sandbox denies reads and writes under the real home, so the Codex output file goes to a scratch folder in `/tmp`, and the lane copies it into the run folder afterwards. stdout and stderr still go straight into the run folder. Don't trust exit 0: the lane now logs a missing last-message file to `agent.err`.
- **Did not apply (not in this repo):** Mistral Vibe and its `--output-dir` flag. This harness has no Vibe lane.
- **Applied as a precaution, not as a fix here:** this repo lives at `/private/tmp/h-A7v2QM`, outside the real home, so the `-o` denial the colleague hit wouldn't happen in this layout. I used the scratch folder anyway, so the lane still works if the run folder ever moves under the home folder.
- **Did not apply:** the colleague's specific failure was a run folder under the home folder, which isn't this setup. I didn't change the profile or the `kimi` lane.

Nothing was committed, deployed, published, or sent to any external service.
