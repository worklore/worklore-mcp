# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same `codex exec` command as the `codex` lane under `sandbox/agent.sb`, with scratch `HOME` and `CODEX_HOME` in `/tmp`. The profile now takes an `AGENT_INSTALL` parameter: Kimi retains access to its installation, while the Codex lane gets no exception under the real home. The Codex final message is written in scratch space and copied to the run folder after the sandbox exits. A successful CLI exit without a nonempty final message is reported as a failure.

The colleague's note applies to Codex's `-o` output: the run folder may be under the denied real home, and `sandbox-exec` would block Codex from writing `final.txt` there. The scratch output and copy after exit follow the note. The shell still opens `agent.log` and `agent.err` redirects outside the sandbox. The note's Mistral Vibe details and existing-run diagnosis do not apply to this repository.

Verified with `bash -n run.sh`, `git diff --check`, and a `sandbox-exec` probe that could not read a file in the real home. I did not run a live Codex task because that would send the task to an external service.
