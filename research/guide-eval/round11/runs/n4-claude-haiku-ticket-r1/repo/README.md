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
  `sandbox/agent.sb` with an empty scratch HOME, like `kimi`. Codex's own
  folder `~/.codex` (login and config) is the only part of the real home the
  profile opens. Codex writes its last message to a scratch folder in `/tmp`
  (a write into the run folder would be denied by the profile), and the lane
  copies it into the run folder. If that file is missing, the lane exits 3.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  macOS sandbox profile `sandbox/agent.sb` (no reading or writing the real
  home), with an empty scratch HOME. Kimi's own install and sessions live in
  `~/.kimi-code`, which the profile opens.

The profile opens only the folder named by `AGENT_HOME`, so one lane's
credentials stay out of the other lane's shell.

Codex on the eval Mac logs in from `~/.codex/auth.json`, not from
`CODEX_API_KEY`, so the sandboxed lane has to open `~/.codex`.
