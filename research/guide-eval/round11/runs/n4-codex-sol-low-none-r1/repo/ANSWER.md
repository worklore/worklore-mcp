Added a `codex-sandboxed` lane to `run.sh`. It runs the same Codex command and produces the same run artifacts as `codex`, but launches it through `sandbox/agent.sb` with an empty temporary `HOME` and `CODEX_HOME`. The temporary home is removed after the run.

Updated the sandbox profile so its `~/.kimi-code` exception applies only to the Kimi lane; the Codex lane has no exception under the real home. Documented the lane in `README.md`.

Verified `run.sh` syntax, checked the diff for whitespace errors, and confirmed a sandboxed shell cannot read the real home's Codex config. I did not start an agent run, which would contact an external service.
