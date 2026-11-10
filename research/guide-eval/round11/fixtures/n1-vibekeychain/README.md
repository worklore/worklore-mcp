# headless Vibe runs (my setup)

I run Mistral Vibe CLI 3.1.0 headless on Devstral 2 through OpenRouter, for batch coding tasks. Each run goes
through `run-vibe.sh`, which starts Vibe inside a macOS sandbox (`agent.sb`) with an empty scratch HOME and an
allowlisted environment, because the agent has a real shell and everything it sees goes to OpenRouter.

- `run-vibe.sh "<prompt>" [workdir]`: one run; `OPENROUTER_API_KEY` comes from my shell (it is set, and it works
  with curl against OpenRouter).
- `agent.sb`: the sandbox. It must keep the agent away from my home folder and the Keychain; that is the whole point.
- `vibe/config.toml`: the Vibe config (OpenRouter provider, Devstral 2).
- `logs/last-run.out`, `logs/last-run.err`: the last run (`./run-vibe.sh "say hi" /tmp/x`, printed `exit 2`).

Every run ends within a second or two with exit 2 and does nothing; no export folder is written.
