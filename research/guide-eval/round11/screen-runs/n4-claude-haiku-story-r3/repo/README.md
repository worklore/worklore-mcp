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
- `codex-sandboxed`: the same Codex run, with codex and its shell under
  `sandbox/agent.sb` and a scratch HOME and `CODEX_HOME`. `-o` writes into a
  scratch folder in `/tmp` and the file is copied into the run folder after
  the sandbox exits, because the profile denies the real home (the eval
  repository sits under it on the eval Mac). `~/.codex/auth.json` and
  `config.toml` are copied into the scratch `CODEX_HOME` before the run.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  macOS sandbox profile `sandbox/agent.sb` (no reading or writing the real
  home), with an empty scratch HOME. Kimi's own install and sessions live in
  `~/.kimi-code`, which the profile opens.

Codex logs in from `~/.codex/auth.json` (`CODEX_API_KEY` and `OPENAI_API_KEY`
are unset on the eval Mac). The unsandboxed `codex` lane reads it from the real
home; `codex-sandboxed` copies it into the scratch `CODEX_HOME`, so its shell
can read that copy.
