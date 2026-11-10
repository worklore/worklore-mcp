# codex-sandbox lane

## What I changed

**`run.sh`**

- Added a `codex-sandbox` lane. It runs the same `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C <scratch> --json -o ... <prompt>` as the `codex` lane.
- The new `codex_sandbox_run` function wraps that command in `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, the same way `kimi_run` does.
- The process gets a fresh scratch HOME (`mktemp -d /tmp/chome-XXXXXX`), which is removed afterwards.
- `CODEX_HOME` is set to `<scratch HOME>/.codex`. Without this, Codex would write its state and sessions under the real `~/.codex`, which the profile blocks.
- The `-o` output file is written into the scratch dir, because Codex writes it from inside the sandbox. After the run, the script copies it to `runs/<task>-codex-sandbox-r<rep>/final.txt`. The run folder sits outside the sandbox, so the copy works even if the harness is located under the real home.
- The header comment lists the new lane.
- The `codex` lane is unchanged.

**`README.md`**

- Documented the new lane next to `codex` and `kimi`.

**`sandbox/agent.sb`**

- Not changed. It already allows only `~/.kimi-code` under the real home, and Codex doesn't need anything there because it reads `CODEX_API_KEY` from the environment.

## How I checked it

No model was called. Running Codex would send the task to an external service, which the ground rules rule out.

1. **Syntax:** `bash -n run.sh` passes.
2. **Sandbox profile**, run directly with `sandbox-exec`:
   - `ls` on the real home → `Operation not permitted`.
   - `touch` in the real home → `Operation not permitted`, and no file was created.
   - Writing to the scratch `CODEX_HOME` → succeeds.
   - `codex --version` runs under the profile (`codex-cli 0.160.0`).
3. **Whole lane, end to end:** I put a stub `codex` first on `PATH` and ran `./run.sh fizz codex-sandbox 9`. The stub:
   - parsed `-o` and wrote the final message,
   - tried to list the real home and got `READ_DENIED`,
   - printed the scratch `HOME` and `CODEX_HOME`.

   The run produced `final.txt`, `agent.log`, `agent.err`, `meta.json` and `answer.json` (the grader's `check_answer.py` read the final message correctly). The scratch dir was removed. I then deleted the test run folder and the stub.

## Not verified

- A real Codex run under the sandbox. I did not run one, because that would send the task to OpenAI. Open question: whether Codex needs any file under the real home beyond what the stub showed. The lane is built on the assumption that it does not, and the README says the same of the `codex` lane.
- Whether `sandbox-exec` (deprecated by Apple, but still present here) keeps working on other macOS versions.

## Files

- `run.sh`: new lane and function.
- `README.md`: lane documentation.
- `ANSWER.md`: this file.

Nothing was committed, deployed, published or submitted.
