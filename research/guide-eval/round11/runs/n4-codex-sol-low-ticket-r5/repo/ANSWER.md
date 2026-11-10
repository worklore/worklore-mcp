# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It uses the same Codex arguments as the
`codex` lane, but runs through `sandbox-exec` with `sandbox/agent.sb`. It sets
scratch `HOME` and `CODEX_HOME` directories under `/tmp`, so Codex and its shell
cannot read or write the real home. I made the profile's agent-directory
exception a parameter: Kimi still gets `~/.kimi-code`, while Codex gets only
its scratch directory. The existing API key from the environment supplies
authentication.

The colleague's Codex output-file finding applies: `-o` must point outside the
profile's denied home path when the repository lives there. This lane writes
`final.txt` to a scratch `/tmp` directory, copies it into the run folder after
Codex exits, and removes both scratch directories. It reports a failed run if
Codex exits successfully without writing the final file. Shell redirection of
`agent.log` and `agent.err` remains in the run folder because those files are
opened before `sandbox-exec` starts. The Mistral Vibe details do not apply here.

Verified with `bash -n run.sh`, `git diff --check`, and a local `sandbox-exec`
probe confirming the Codex profile blocks reading both `~/.codex/auth.json`
and `~/.kimi-code`. I did not
run a Codex task because that would send its prompt to an external service.
