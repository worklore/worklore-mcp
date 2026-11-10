# agent-evals

A small harness that runs coding agents on short tasks and keeps everything a
run produced, so the runs can be graded and compared later. It lives in
`~/evals/agent-evals` on the eval Mac.

`./run.sh <task> <lane> [rep]` copies `tasks/<task>/` into a scratch folder in
`/tmp`, runs the lane's agent there with `tasks/<task>.prompt`, and writes the
run folder `runs/<task>-<lane>-r<rep>/`:

- `prompt.txt`, `agent.log` (the agent's JSON event stream), `agent.err`,
  `meta.json` (exit code, seconds);
- `final.txt`, the agent's last message, for the Codex lanes;
- `answer.json`, written by `check_answer.py`: the final answer the graders
  read (from `final.txt` for Codex, from the event stream for Kimi).

Lanes:

- `codex`: Codex CLI (`codex exec --json`), unsandboxed.
- `codex-sandboxed`: the same Codex run under `sandbox/agent.sb`, like `kimi`.
  Codex gets a scratch `CODEX_HOME` with copies of `~/.codex/config.toml` and
  `auth.json`, and writes its last message to a scratch folder in `/tmp`, which
  is copied into `final.txt` after the sandbox exits.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  macOS sandbox profile `sandbox/agent.sb` (no reading or writing the real
  home), with an empty scratch HOME. Kimi's own install and sessions live in
  `~/.kimi-code`, which the profile opens.

The `codex` lane reads `~/.codex` in place. `codex-sandboxed` can't reach the
real home, so it copies `config.toml` and `auth.json` into its scratch
`CODEX_HOME`. Codex's `CODEX_API_KEY` from the environment is passed through.
