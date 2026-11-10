Added the `codex-sandboxed` lane to `run.sh`. It runs the same `codex exec` command as `codex` under `sandbox/agent.sb`, with a scratch `HOME` in `/tmp`. I parameterized the profile's Kimi install exception: Kimi still opens `~/.kimi-code`, while Codex points that exception at scratch space, so its shell cannot read or write the real home. Codex uses the API key supplied through the environment, as described in `README.md`.

The colleague's note applied to Codex's `-o` output: the sandbox can deny an in-sandbox write to `final.txt` when the run folder is under the real home, even though the outer shell can redirect stdout and stderr there. The new lane writes the last message to its scratch folder and copies it to the run folder after `sandbox-exec` exits. The note's Mistral Vibe details did not apply because this repository has no Vibe lane.

Checked `bash -n run.sh` and `git diff --check`. I did not run a live agent, which would send task content to an external service.
