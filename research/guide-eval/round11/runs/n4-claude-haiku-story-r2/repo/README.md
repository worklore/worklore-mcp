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
- `codex-sandboxed`: the same Codex run, but its output goes to OpenAI, so it
  runs under `sandbox/agent.sb` like kimi (no reading or writing the real
  home), with an empty scratch HOME. Its `-o` file goes to a scratch folder in
  `/tmp` and is copied into the run folder after the run.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  macOS sandbox profile `sandbox/agent.sb` (no reading or writing the real
  home), with an empty scratch HOME. Kimi's own install and sessions live in
  `~/.kimi-code`, which the profile opens.

The profile opens one state folder per lane, passed as `-D STATE=...`: kimi's
`~/.kimi-code`, codex-sandboxed's `~/.codex`. Codex-sandboxed reads its config
and login from `~/.codex`, because this machine has no `CODEX_API_KEY` set.
That means the sandboxed shell can read `~/.codex/auth.json`, as kimi's shell
can read its own credentials.
