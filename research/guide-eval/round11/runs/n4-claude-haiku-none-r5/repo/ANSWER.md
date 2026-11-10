# codex-sandboxed lane

`./run.sh <task> codex-sandboxed [rep]` runs the same Codex command as the `codex` lane
(`codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C <scratch> --json -o final.txt`),
but the whole process runs under `sandbox/agent.sb` with an empty scratch HOME, the same way the `kimi` lane does.

## What changed

- **`run.sh`**: new `codex_sandboxed_run` function and `codex-sandboxed)` case. It needs `CODEX_API_KEY`
  in the environment and exits with code 3 (recorded in `meta.json`, reason in `agent.err`) if it is missing.
  The `codex` and `kimi` lanes keep their existing commands; the kimi lane only gets the new `AGENT_DIR` argument.
- **`sandbox/agent.sb`**: the kimi carve-out was hard-coded to `~/.kimi-code`, so every sandboxed shell
  could read and write it. I replaced it with `-D AGENT_DIR=...`. Each lane opens only its own directory:
  kimi opens `~/.kimi-code`, codex-sandboxed opens the scratch HOME (already writable, so effectively nothing).
  Without this change, the codex lane's shell could have read Kimi's files. This is a change to the shared profile,
  so review it as such.
- **`README.md`**: lane list and the profile's parameters. The old note said Codex "needs nothing from the home
  folder", which is wrong for the `codex` lane on this machine: it logs in from `~/.codex/auth.json`.

## Why CODEX_API_KEY

On this machine Codex authenticates from `~/.codex/auth.json`. The profile denies that file to the agent's shell,
so the sandboxed lane has to take its key from the environment. The lane fails fast if the key is unset,
rather than starting Codex with no credentials.

## Verification

Checked without making any model call, since a full run sends the task to OpenAI:

- `bash -n run.sh` passes.
- `env -u CODEX_API_KEY ./run.sh fizz codex-sandboxed 9` exits with code 3 and writes `meta.json` (run folder removed afterwards).
- Under the profile with the codex lane's arguments: `codex --version` runs, and reads of `~/.codex/auth.json`
  and `~/.kimi-code`, and writes into `~/`, are denied. Writes to the scratch HOME are allowed.
- Under the profile with the kimi lane's arguments: `kimi --version` runs (2.5.2), and `~/.kimi-code/bin/rg` is readable.
- Before the change, the shared profile allowed `cat ~/.kimi-code/bin/rg` from any sandboxed shell. It is now denied for the codex lane.

Not verified: a complete `codex exec` run in the sandbox. Run `./run.sh fizz codex-sandboxed 1` with
`CODEX_API_KEY` set to check it end to end. I did not do that because it sends the task to OpenAI.

## Differences from the `codex` lane

- Auth comes from `CODEX_API_KEY`, not `~/.codex/auth.json`.
- Codex starts with a fresh scratch `~/.codex`, so `~/.codex/config.toml` settings (model, provider, profiles,
  project trust) are not applied. Compare the runs' `agent.log` if that matters for grading.
- `--dangerously-bypass-approvals-and-sandbox` is kept, as in the `codex` lane. Codex's own sandbox is off,
  so the OS profile is the only fence. This is the same arrangement the kimi lane uses.
- Network is open, as in `agent.sb` for kimi.

Nothing was committed, deployed, or sent to any external service.
