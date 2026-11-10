# codex-sandboxed lane

`./run.sh <task> codex-sandboxed [rep]` runs the same `codex exec` command as the `codex` lane (same flags, prompt,
timeout, `--json` log, `-o final.txt`), wrapped the way `kimi` is: `HOME` set to an empty scratch dir in `/tmp`, and
`sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`. Codex's key comes from `CODEX_API_KEY` in the environment,
so it needs nothing from the real home.

## Changes
- **run.sh**: new `codex_sandboxed_run` and a `codex-sandboxed)` case; lane listed in the usage comment.
  - Codex writes `-o` itself, from inside the sandbox, and on the eval Mac `runs/` sits under the real home
    (`~/evals/agent-evals`), so a write straight to `$R/final.txt` would be denied. Codex writes it to a scratch dir
    instead and the script copies it into the run folder afterwards. `agent.log` and `agent.err` are fine as they are,
    because bash opens those redirects before `sandbox-exec` starts.
  - The scratch HOME and output dir are deleted at the end, as in `kimi`.
- **sandbox/agent.sb**: the one directory the profile opens was hard-coded to `~/.kimi-code`. Used as-is, that would
  let the Codex agent read Kimi's install and credentials and send them to OpenAI. The opened directory is now a
  parameter, `-D AGENT_DIR=...`. `kimi` passes `~/.kimi-code`, so it gets the same rules as before. `codex-sandboxed`
  passes its scratch HOME, which is outside the real home, so nothing in the real home is opened.
- **README.md**: describes the new lane.

## Checked
- `bash -n run.sh` passes.
- I ran the full `./run.sh fizz codex-sandboxed` with a stand-in `codex` script first on PATH, so nothing was sent to
  OpenAI. Inside the sandbox it could not read `~/.codex/config.toml` or `~/.kimi-code`, and could not write to `~`.
  It could write to the scratch HOME and the task workdir. `final.txt` was copied out, `answer.json` read it
  (`source: final.txt`) and `rc=0`. The test run folder and stub were deleted afterwards.
- The real `codex --version` runs under the profile with a scratch HOME.
- With `AGENT_DIR=~/.kimi-code`, the profile still opens `~/.kimi-code` and still blocks `~/.codex`.

## Not checked / differences from `codex`
- I didn't do a real Codex run, because that sends the task to OpenAI. Run `./run.sh fizz codex-sandboxed` once on the
  eval Mac to confirm.
- `codex` reads `~/.codex/config.toml`, which on this machine loads the pencil/posthog MCP servers and plugins.
  `codex-sandboxed` starts with an empty CODEX_HOME, so it uses default config with none of those. The config sets no
  model, so the model should be the same.
- Codex's own sandbox is still bypassed (`--dangerously-bypass-approvals-and-sandbox`), as in `codex`. Seatbelt
  doesn't nest, so the fence here is `agent.sb`. Network stays open, as it does for `kimi`.
- Shell commands still see `/tmp` and the rest of the filesystem outside the home, as with `kimi`.
