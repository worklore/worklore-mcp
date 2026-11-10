# ANSWER: codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed` (`codex_sandboxed_run`). It runs the same
  `codex exec` command as the `codex` lane, wrapped the way `kimi_run` wraps kimi:
  `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, with a scratch `HOME` and a
  scratch `CODEX_HOME` in `/tmp`.
  - `-o` writes to `$SCR/final.txt` in `/tmp`. After `sandbox-exec` returns, the file is
    copied to `runs/<task>-codex-sandboxed-r<rep>/final.txt`, and the scratch folders are removed.
  - Stdout and stderr are redirected into the run folder by the outer shell, before `sandbox-exec` starts.
  - If `final.txt` is missing or empty after the run, the lane prints a warning.
- **`README.md`**: documents the new lane. I also corrected a wrong claim. It said codex
  logs in with `CODEX_API_KEY` and needs nothing from the home folder. On this machine
  both `CODEX_API_KEY` and `OPENAI_API_KEY` are unset, and codex logs in from
  `~/.codex/auth.json`.
- **`sandbox/agent.sb`**: unchanged. The kimi lane already uses it.

## Verification

- `bash -n run.sh` passes.
- Sandbox probe with the unchanged profile:
  - `cat ~/.codex/config.toml` fails with "Operation not permitted".
  - `touch ~/probe-denied` fails, and the file was not created.
  - A write to `/tmp` succeeds.
  - The codex binary (`/opt/homebrew/bin/codex`) resolves outside the real home.
- Smoke run `./run.sh fizz codex-sandboxed 1`:
  - `meta.json` has `exit_code: 0`, 23 s.
  - `final.txt` is non-empty (231 chars). `answer.json` reads it (`source: final.txt`).
  - `agent.err` has 0 "Operation not permitted" lines.
- Not verified: the kimi lane, and the codex lane (unchanged, not re-run). I did not
  test a `-o` write into a denied path, so the "lost answer" failure is not reproduced here.

## Which parts of the colleague's note applied

- **Applied: the `-o` output path.** On the eval Mac the README puts the harness under
  `~/evals`, so `runs/` is inside the real home, which the profile denies. The
  colleague's bug would hit a `-o "$R/final.txt"` write there. So the lane writes to
  `/tmp` and copies the file out after the sandbox exits.
- **Applied: keep stdout and stderr redirects outside the sandbox.** The outer shell
  opens them before `sandbox-exec` starts.
- **Applied: don't trust the exit code alone.** The lane checks that `final.txt` is
  non-empty and warns if it is not. I also grepped `agent.err` for "Operation not permitted".
- **Did not apply here: the path comparison.** This clone is at `/private/tmp/h-VoLmXu`,
  outside the real home, so the profile would not deny `runs/` here. The copy-out is
  still needed for the eval-Mac layout.
- **Did not apply: Mistral Vibe.** The `--output-dir` and Vibe details are not used by this harness.
- **Ground rules.** I made no deployment, publish, or report. The smoke run did send
  the `fizz` task to OpenAI through codex. That is the lane's normal purpose, not an
  extra external action.

## Open issues and limits

1. **The agent's shell can read the login token.** Codex needs `auth.json` to start, and
   the copy in the scratch `CODEX_HOME` is in `/tmp`, which the profile allows. Network
   is also open. So a shell command could read and send the token. This is the same
   exposure the kimi lane has for `~/.kimi-code`. A stricter option is a dedicated,
   scoped API key passed as `CODEX_API_KEY`. Codex drops variables matching KEY/TOKEN
   from the shell environment by default, though that is not verified here. That would
   change how the lane authenticates, so I did not do it.
2. **MCP servers from the real home are unavailable in this lane.** The copied
   `config.toml` still lists the `pencil` server, which lives under `~/.pencil`, and
   the posthog plugin. The smoke run logged posthog `AuthRequired` errors. The sandbox
   blocks the real home, so this is expected. The unsandboxed `codex` lane has these tools.
3. **Only `auth.json` and `config.toml` are copied.** Any other state under `~/.codex`
   (plugins, sessions, sqlite) is not present in the scratch `CODEX_HOME`. Codex
   started and finished without it on the smoke run.
