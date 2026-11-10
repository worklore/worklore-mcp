# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command and flags as `codex` inside `sandbox/agent.sb`, with a scratch `HOME` and `CODEX_HOME`. The profile now takes a lane-specific exception: Codex gets its scratch home, while Kimi retains access to its install. This keeps the real home closed to the Codex agent. Codex writes its final message to the scratch directory; after the sandbox exits, the lane copies it to the run folder. A missing or empty final message now makes an otherwise successful run fail.

Updated `README.md` with the new lane. `bash -n run.sh` and `git diff --check` pass. I did not run a live Codex smoke test because it would contact an external service.

The colleague's note applies to Codex's `-o` output path: the run folder can be under the denied real home, and an exit code of zero alone does not prove the final message was saved. The scratch output and copy step, existing outer-shell log redirection, and final-file check follow that finding. Its Mistral Vibe details do not apply to this harness.
