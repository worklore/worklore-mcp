# Answer

Added the `codex-sandboxed` lane to `run.sh`. It uses the same Codex arguments and output files as `codex`, but launches Codex through `sandbox-exec` with `sandbox/agent.sb` and a temporary scratch `HOME`. The sandbox receives the real home path for its access rules, and the scratch home is removed after the run.

Updated `README.md` with the new lane. Verified `run.sh` with `bash -n` and checked the diff with `git diff --check`. I did not run an agent, since that would contact an external service.
