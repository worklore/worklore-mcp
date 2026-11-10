# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It uses the same Codex arguments and JSON event stream as `codex`, but launches Codex through `sandbox-exec` with `sandbox/agent.sb` and an empty scratch `HOME`. The profile receives the real home path through `-D HOME`, so the agent's shell cannot read or write it. I parameterized the profile's Kimi install exception: Kimi retains access to its installation, while Codex grants no exception under the real home. The lane writes Codex's last message to a temporary folder in `/tmp`, then moves it to the run folder as `final.txt` after Codex exits. `check_answer.py` therefore reads it without changes. The new lane is also listed in `README.md`.

The colleague's note applied to Codex's `-o` output file: Codex opens that file inside the sandbox, whereas the shell opens `agent.log` and `agent.err` redirects before `sandbox-exec` starts. It also applied to using `/tmp` scratch space outside the denied home path and copying the final answer afterward. The note's Mistral Vibe details did not apply because this repository has no Mistral lane.

Verified with `bash -n run.sh`, `git diff --check`, and a local `sandbox-exec` profile load. I did not run a live Codex task, which would contact an external model provider.
