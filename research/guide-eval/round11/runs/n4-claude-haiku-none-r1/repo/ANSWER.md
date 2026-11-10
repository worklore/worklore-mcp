# Answer: codex-sandboxed lane

## What I changed

- **`run.sh`**: added a `codex-sandboxed` lane. It runs the same `codex exec`
  command as the `codex` lane (same flags, same prompt, same `-o final.txt`,
  same timeout), but wraps it in `sandbox-exec -f sandbox/agent.sb` the way the
  `kimi` lane does. The `codex` and `kimi` lanes are unchanged.
- **`README.md`**: listed the new lane, and corrected the Codex login note.
  On this machine Codex logs in with `~/.codex/auth.json`, not `CODEX_API_KEY`.
- **`sandbox/agent.sb`**: not changed. It already denies reads, writes and
  listing of `$HOME` and opens nothing under `~/.codex`.

## How the lane keeps the real home out of reach

1. A scratch home `/tmp/khome-XXXXXX` is created and used as `HOME`.
2. Codex can't read its login from the real home under the profile, so the
   lane sets `CODEX_HOME` to `<scratch>/.codex` and copies in `auth.json`,
   `config.toml` and `installation_id`.
3. The whole `codex exec` process runs under the profile with
   `-D HOME=<real home>`. The agent's shell commands are children of that
   process, so they inherit the same profile.
4. The scratch home is removed when the run ends.

## What I checked

- **Profile behavior** (run directly under `sandbox-exec`): reading
  `~/.codex/auth.json` fails with "Operation not permitted", listing `~` fails,
  writing into `~` fails, and writing to `/tmp` works.
- **Real run**: `./run.sh fizz codex-sandboxed 1` exited 0 in 23 s and wrote
  `runs/fizz-codex-sandboxed-r1/` (`final.txt`, `agent.log`, `agent.err`,
  `meta.json`, `answer.json`). The agent read `fizz.py`, found that multiples of
  15 hit the "Fizz" branch first, fixed the copy in its scratch folder, and ran
  the script to confirm `FizzBuzz`. The answer is in `final.txt`.
- The repo's `tasks/fizz/fizz.py` is unchanged.
- `bash -n run.sh` passes.

I did not exercise the agent's own shell against the real home from inside a
Codex run. The check above was done directly against the profile, and the
inheritance behavior is standard for macOS sandbox profiles.

## Things to know

- **The agent's shell can read the login copy.** `auth.json` is copied into
  `/tmp` so that Codex can authenticate. The agent's shell is not blocked from
  that scratch folder, so it could read the token during a run. This is not the
  real home, but it is a credential reachable from the sandbox. If that matters,
  the next step is to use an API key via `CODEX_API_KEY` instead of a login
  file, which the lane would then not need to copy.
- **Token refresh.** `auth.json` was last modified on Nov 4 (file mtime), so a
  token refresh could happen during a run. If the refresh token rotates, the scratch copy
  would hold the new one and the real `~/.codex/auth.json` could be left with a
  stale one. I did not check whether that happened in this run, and I did not
  look at the token contents.
- **MCP plugins.** The copied `config.toml` still lists MCP servers that live
  under the real home (`~/.pencil`, plus PostHog and GitHub plugins). Under the
  profile they fail to start or authenticate. Codex logs those errors in
  `agent.err`, and the run completes anyway. This is the expected price of the
  fence.
- **Run output.** The test run is in `runs/fizz-codex-sandboxed-r1/`. `runs/*`
  is gitignored, so nothing was committed or published. No external service was
  used beyond the Codex API call that the lane exists to make.

Nothing has been committed.
