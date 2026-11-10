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

- `codex`: Codex CLI (`codex exec --json`), unsandboxed, using its usual login
  (`~/.codex/auth.json`).
- `codex-sandboxed`: the same Codex run, but its shell runs under
  `sandbox/agent.sb` with an empty scratch HOME. The sandbox blocks the real
  home, so auth must come from `CODEX_API_KEY` in the environment; the lane
  exits with code 3 if it is unset.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  same profile, with an empty scratch HOME. Kimi's own install and sessions
  live in `~/.kimi-code`, which the profile opens for this lane only.

The profile takes `-D HOME=<real home>` and `-D AGENT_DIR=<the one directory
the lane's agent needs>`. Only `AGENT_DIR` is opened, so the codex lane's
shell cannot reach `~/.kimi-code` either.
