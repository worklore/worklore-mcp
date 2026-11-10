# codex-sandboxed lane

`./run.sh <task> codex-sandboxed [rep]` runs exactly the `codex` lane's command
(`codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C $W --json -o ... "$P"`,
same timeout), but the way the kimi lane does it:

- an empty scratch HOME (`mktemp -d /tmp/chome-XXXXXX`), with `CODEX_HOME=$SCRATCH/.codex`,
  removed after the run. Codex logs in via `CODEX_API_KEY` from the environment, so it
  needs nothing from `~/.codex`; the binary is in `/opt/homebrew`, outside the home.
- wrapped in `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, so Codex and
  every shell it spawns can't read or write the real home.

## Details that differ from a plain copy of the codex lane

1. **`-o final.txt` goes to the scratch HOME, then is copied into the run folder.** The run
   folder lives under the real home on the eval Mac (`~/evals/agent-evals/runs/...`), so a
   sandboxed Codex couldn't write it there. (`agent.log`/`agent.err` are fine: those
   redirections are opened by bash before `sandbox-exec` runs.)
2. **Codex's own sandbox stays bypassed.** Its seatbelt sandbox can't be nested inside
   `sandbox-exec`, so `agent.sb` is the fence, as with kimi.
3. **`agent.sb` now takes the opened directory as a parameter.** It used to always open
   `~/.kimi-code`, so a Codex agent under it could have read Kimi's install, config and
   sessions. Now it opens `-D AGENT_DIR=<dir>`: the kimi lane passes `$HOME/.kimi-code`
   (same behavior as before), and codex-sandboxed passes its scratch HOME, so nothing in
   the real home is opened.

The README's lane list and the `run.sh` header are updated too.

## Verification (no real Codex/OpenAI calls were made)

- `codex --version` runs fine under the profile.
- Ran `./run.sh fizz codex-sandboxed` with a stub `codex` first on PATH. Inside the
  sandbox, reading `~/.codex/config.toml`, `~/.zshrc` and `~/.kimi-code` was blocked, writing
  to the real home was blocked, writing to the workspace and to the scratch `CODEX_HOME` worked,
  and `final.txt` → `answer.json` came through (`"source": "final.txt"`). Scratch HOME removed.
- The kimi profile invocation still lists `~/.kimi-code` and still blocks `~/.zshrc`.
- Not yet done: a real end-to-end Codex run (it would call OpenAI). First real run to try:
  `./run.sh fizz codex-sandboxed`. If Codex fails, look in `agent.err` for something it wants
  from the home folder.
- Note: as with kimi, the profile still allows file *metadata* under the home: an agent can
  stat a path it already knows (check that it exists, see its size). It can't read contents
  or list directories.
