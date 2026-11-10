# ANSWER: codex-sandbox lane

## What I changed

**`run.sh`**

- Added a `codex-sandbox` lane. It runs the same `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json -o final.txt "$P"` command as the `codex` lane, with the same timeout and output files.
- The new function `codex_sandbox_run` follows the kimi lane's pattern:
  - `HOME` is set to an empty scratch dir under `/tmp`, and the real home is passed in as `-D HOME=<real home>`.
  - The whole `codex` process runs under `sandbox-exec -f sandbox/agent.sb`, so its shell is fenced too.
  - `CODEX_HOME` points at an empty `.codex` inside the scratch dir. Codex keeps its state there, so the real `~/.codex` is never opened. The scratch dir is removed afterwards.
- The `codex` and `kimi` lanes are unchanged. The `case` dispatch gained one line.
- The header comment lists the new lane.

**`README.md`**: added a `codex-sandbox` entry to the lane list.

`sandbox/agent.sb` is unchanged. Its existing rules already deny reads and writes under `HOME`, and the `.kimi-code` allow rules don't matter for Codex.

## Why `CODEX_HOME` and not an allow rule

Opening `~/.codex` in the profile would let the agent's shell read the real Codex state and credentials. Pointing `CODEX_HOME` at an empty scratch dir avoids that, and it is the Codex equivalent of the kimi lane's `KIMI_CODE_HOME`.

## Auth: a known gap

The README says Codex authenticates from `CODEX_API_KEY` in the environment. In this shell that variable is **not set**. The only Codex credential I can see is `~/.codex/auth.json`, and the sandbox correctly blocks it. So:

- On a machine where `CODEX_API_KEY` is exported, `codex-sandbox` should authenticate like `codex`.
- Here, a real `codex-sandbox` run would fail at login.

I did not copy `auth.json` into the scratch dir. That would give the agent's shell the real credential, which defeats the point of the lane.

## Verification (local only, no API calls)

1. `bash -n run.sh`: syntax OK.
2. Sandbox probe with the real profile:
   - `cat ~/.codex/config.toml` → *Operation not permitted* (denied).
   - Creating a file in `~` → denied; nothing was created.
3. `codex --version` under the profile with scratch `HOME` and `CODEX_HOME` → `codex-cli 0.160.0`, exit 0. Before I added `mkdir` for `$SH/.codex`, this printed a "CODEX_HOME does not exist" warning; the lane now creates the directory.
4. Wiring test: `PATH=<stub dir>:$PATH ./run.sh fizz codex-sandbox 9`, with a stub `codex` that only records its environment and tries to read the real `~/.codex/auth.json`:
   - `HOME` and `CODEX_HOME` pointed into `/tmp/khome-*`.
   - The real `auth.json` read was denied.
   - `meta.json`, `final.txt`, and `answer.json` were produced.
   - No scratch dirs were left behind.
   - I deleted the test run folder afterwards.

I did **not** run a real Codex task. That would send the fizz prompt to OpenAI, and you asked for the lane, not an eval run. To try it for real, export `CODEX_API_KEY` and run `./run.sh fizz codex-sandbox 1`.

## Not done / open points

- The stub test proves the fence and env wiring. It does not prove Codex's own tool calls behave correctly under the profile, since that needs a real run.
- `check_answer.py` is unchanged. The new lane writes `final.txt`, which it already reads first, so no change is needed.
