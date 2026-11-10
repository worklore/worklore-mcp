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
- `codex-sandboxed`: the same Codex run, but its process and shell run under
  `sandbox/agent.sb` with an empty scratch HOME and `CODEX_HOME`. Nothing under
  the real home is opened, so it needs `CODEX_API_KEY` in the environment; the
  ChatGPT login in `~/.codex` is out of its reach. It does not load the real
  `~/.codex/config.toml`, so that config's MCP servers and plugins are absent.
- `kimi`: Kimi Code. Its output goes to Moonshot, so its shell runs under the
  macOS sandbox profile `sandbox/agent.sb` (no reading or writing the real
  home), with an empty scratch HOME. Kimi's own install and sessions live in
  `~/.kimi-code`, which the profile opens.

The profile takes the one real-home path a lane may open as `-D OPEN=<path>`:
kimi opens `~/.kimi-code`, `codex-sandboxed` opens its scratch dir.

The plain `codex` lane logs in with the ChatGPT login in `~/.codex`.
