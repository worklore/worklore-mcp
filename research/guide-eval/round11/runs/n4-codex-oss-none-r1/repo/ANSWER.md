## Changes Made

- Updated the lane documentation in `run.sh` to include a new lane **codex-sandboxed**.
- Implemented `codex_sandboxed_run` function that runs the Codex CLI inside `sandbox/agent.sb`, providing an isolated `$HOME` similar to the existing `kimi` lane.
- Modified the case statement to dispatch the new lane.
- Preserved existing functionality for the original `codex` and `kimi` lanes.

The sandboxed lane mirrors the unsandboxed Codex run but executes it under the sandbox profile, ensuring the agent cannot read or write the real home directory.
