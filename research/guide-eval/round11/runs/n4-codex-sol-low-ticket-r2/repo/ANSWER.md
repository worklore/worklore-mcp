# Codex sandbox lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command and flags as `codex`, inside `sandbox/agent.sb`, with a temporary `HOME` and `CODEX_HOME`. Codex writes its `-o` final message into that temporary directory; the runner copies it to the run folder after the sandboxed process exits and then removes the temporary directory. The existing log redirects and answer grading remain the same.

The shared sandbox profile now takes an `AGENT_DIR` parameter. Kimi passes its existing `~/.kimi-code` exception; Codex passes its temporary directory, so its shell has no exception inside the real home. `README.md` lists the new lane.

The colleague's note applied to the `-o` output path and to stdout/stderr redirects: the CLI's own final-message write must target a path writable inside the sandbox, while the runner's redirects can still target the run folder. The `/tmp` scratch-directory approach applied. The Mistral Vibe details did not apply because this repository has no Mistral lane. This repository's run folder is currently outside the real home, but the scratch output also works when the harness lives under the real home.

Verification: `bash -n run.sh` and `git diff --check` passed. A local mock Codex run through `codex-sandboxed` confirmed that reading a file in the real home was denied and that `answer.json` received the final message from `final.txt`. I did not invoke the real Codex CLI, which would contact an external service.
