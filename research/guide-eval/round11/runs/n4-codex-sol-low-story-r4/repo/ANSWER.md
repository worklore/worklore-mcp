# Codex sandboxed lane

Added `codex-sandboxed` to `run.sh`. It runs the same Codex command as `codex` under `sandbox/agent.sb`, with a scratch HOME. The lane writes Codex's `-o` file in `/tmp`, copies it to the run folder after the sandbox exits, and reports failure if the final answer is missing or empty. `agent.log` and `agent.err` still go directly to the run folder.

The note's output-file issue applied: the sandbox denies writes to a run folder under the real home, and Codex can exit successfully even when `-o` fails. Its scratch-output and post-run-copy fix applies here. The note's Mistral Vibe details and existing failed-run diagnosis did not apply. I also made the profile's `~/.kimi-code` allowance specific to the Kimi lane, so the Codex lane cannot read or write that part of the real home.

Verified `bash -n run.sh`, that `sandbox-exec` accepts the profile with the Codex lane's parameters, and a local mock Codex run. The mock run returned exit code 0, produced `answer.json` from `final.txt`, and left `agent.err` empty. No provider-backed smoke run was made because this task prohibits reporting to external services.
