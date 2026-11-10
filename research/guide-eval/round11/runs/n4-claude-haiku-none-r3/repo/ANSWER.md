# codex-sandboxed lane

## What I changed

- **`run.sh`**
  - Added a `codex-sandboxed` lane. It runs the same `codex exec` command as the `codex` lane, under `sandbox-exec -f sandbox/agent.sb`, the same way the `kimi` lane does.
  - The sandboxed run gets an empty scratch `HOME` in `/tmp`, with `CODEX_HOME` pointing inside it. The real home is passed as `-D HOME=…`, so the profile denies reads and writes there.
  - The command line is now built once in a `CODEX_CMD` array and shared by both Codex lanes, so the two lanes cannot drift apart. The `codex` lane's behaviour is unchanged.
  - The lane exits with an error if neither `CODEX_API_KEY` nor `CODEX_ACCESS_TOKEN` is set. The run is still recorded in `meta.json` with exit code 2.
- **`README.md`**: documented the new lane. I also corrected the old claim that Codex "needs nothing from the home folder". On this machine it does not, as explained below.

## Why the credential comes from the environment

The `codex` lane logs in with the ChatGPT token in `~/.codex/auth.json`. `CODEX_API_KEY` is not set here. The sandbox has to hide that file, because the agent's shell inherits the same sandbox and could read it. So the sandboxed lane takes its credential from the environment instead, using the auth variables that the installed Codex CLI (0.160.0) accepts.

Trade-offs:

- The key is visible to the agent's shell through its environment. That is unavoidable if the agent is to authenticate at all.
- Codex's `config.toml` is not read in the sandboxed lane. The `codex` lane does read it, along with its MCP servers and plugins. So the two lanes are the same Codex invocation, but not the same configuration.

## Verification

I did not run a real Codex agent. That would send the task to OpenAI and spend tokens, and I was asked not to report anything to external services. Instead I checked the following locally:

- `bash -n run.sh` passes.
- **Sandbox profile**, run with the real home as `HOME`:
  - reading `~/.codex/auth.json`: denied (exit 1);
  - listing the real home: denied (exit 2);
  - creating a file in the real home: denied (exit 1);
  - `codex --version` under the profile with a scratch `CODEX_HOME`: works.
- **Guard**: with no credential set, `./run.sh fizz codex-sandboxed 1` writes exit code 2 to `meta.json` and makes no API call.
- **Lane plumbing**: I used a stub `codex` on `PATH`, which makes no network calls. Under `codex-sandboxed`, the stub saw only the scratch `HOME`, and it could neither read the real `auth.json` nor list the real home. The same stub under the `codex` lane could read both, so the test does distinguish the two lanes.

I removed the stub and the test run folders afterwards. Nothing was committed.

## Not covered

- A real end-to-end Codex run under the sandbox is untested. The first real run should confirm that Codex accepts the environment credential and completes the task.
- The sandbox profile is `(allow default)` with the network left open. An agent in the sandboxed lane can still read anything outside the real home, including its own environment, and can send it over the network. The profile only protects the real home.
- Pre-existing, not changed: `run.sh` always exits 0, because its last command is an `echo`. Callers must read `meta.json` for the real exit code.
