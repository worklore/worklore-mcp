# Codex sandbox lane

Added `codex-sandboxed` to `run.sh`. It uses the same Codex arguments as the `codex` lane, but runs through `sandbox/agent.sb` with a temporary HOME in `/tmp`. Codex writes its final message there; after the sandbox exits, the runner copies it to the run folder. If Codex exits successfully without producing that file, the lane reports a failure. Updated `README.md` with the new lane.

The colleague's note applied to the sandbox's denial of writes under the real home, especially Codex's `-o` output file. The temporary output path and post-run copy address that. The note's Mistral Vibe details and hidden-test results did not apply to this repository.

Verified with `bash -n run.sh`, `git diff --check`, and a direct `sandbox-exec` check that the profile denies reading a file in the real home. An attempted mock end-to-end run was rejected by automatic approval review because its command included temporary-file cleanup, so no mock run or external Codex run was performed.
