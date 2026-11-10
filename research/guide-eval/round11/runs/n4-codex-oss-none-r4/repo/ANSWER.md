Added a new lane `codex-sandboxed` to `run.sh`.

* Updated lane documentation to include the new lane.
* Implemented `codex_sandboxed_run` which runs the Codex CLI inside the existing `sandbox/agent.sb` profile, mirroring the unsandboxed `codex` lane but with a temporary sanitized HOME.
* Integrated the new lane into the case statement.

The sandboxed lane behaves like the original `codex` lane while preventing the agent from reading or writing the real home directory.
