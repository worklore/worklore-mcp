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
- `codex-sandboxed`: the same Codex run, but its shell runs under
  `sandbox/agent.sb` with an empty scratch HOME (`CODEX_HOME` inside it), so
  the agent cannot read or write the real home. Codex's own login
  (`~/.codex/auth.json`) is in the real home and is therefore out of reach, so
  this lane needs `CODEX_API_KEY` or `CODEX_ACCESS_TOKEN` set in the
  environment; it exits with an error (recorded in `meta.json`) if neither is
  set. Codex's `config.toml` is not read in this lane either.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  macOS sandbox profile `sandbox/agent.sb` (no reading or writing the real
  home), with an empty scratch HOME. Kimi's own install and sessions live in
  `~/.kimi-code`, which the profile opens.

The `codex` lane needs nothing from the home folder beyond its own login
(`~/.codex`), which it reads unsandboxed.
