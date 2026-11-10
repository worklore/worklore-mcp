# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It uses the same `codex exec` options as the existing `codex` lane, but runs under `sandbox/agent.sb` with an empty temporary `HOME`. The profile now takes a lane-specific `INSTALL` parameter: Kimi retains access to `~/.kimi-code`, while Codex receives no exception inside the real home.

Codex writes `-o` to a temporary folder in `/tmp`. After `sandbox-exec` returns, the lane copies `final.txt` into the run folder and removes its temporary home and output folder. This preserves the final answer for `check_answer.py` even when the run folder is under the protected home.

The colleague's note applied to the `-o` output path, copying the result after the sandbox exits, and keeping stdout and stderr redirects on the outer shell. Its Mistral Vibe details and existing-run diagnosis did not apply here. No live agent run was made because that would contact an external service.

Verified with `bash -n run.sh`, `git diff --check`, and a local `sandbox-exec` probe that denied reads and writes under a protected test path. The Codex lane itself has not been smoke tested against the provider.
