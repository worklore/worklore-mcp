# Answer: codex-sandboxed lane

## What I changed

1. **`sandbox/agent.sb`**: the profile's one hardcoded exception (`~/.kimi-code`) is now a parameter, `-D STATE=<dir>`.
   Everything else is unchanged: `HOME` is denied for reads and writes, network stays open, and the `launchctl`,
   `security` and `osascript` exec denials are still there. Each lane opens only its own state folder, so kimi
   still cannot reach `~/.codex`.
2. **`run.sh`**:
   - `kimi` now passes `-D STATE="$REAL/.kimi-code"`. Its behavior is the same as before.
   - New lane `codex-sandboxed` (`codex_sandboxed_run`). It runs the same `codex exec` command as the `codex` lane, with:
     - `sandbox-exec -D HOME=<real home> -D STATE=<real home>/.codex -f sandbox/agent.sb`;
     - an empty scratch `HOME` in `/tmp`, and `CODEX_HOME` set to the real `~/.codex`, so the config and login are the same as the `codex` lane's;
     - `-o` writing to a scratch folder in `/tmp`, then copying `final.txt` into the run folder after `sandbox-exec` returns;
     - a warning on stderr if `agent.err` contains "Operation not permitted".
   - The unsandboxed `codex` lane is unchanged.
3. **`README.md`**: lane list updated. The old claim that Codex "needs nothing from the home folder" was wrong for this
   machine (see below), so I replaced it.

## Which parts of the colleague's note applied

- **Applied: the `-o` output file.** Codex writes its last message to the `-o` path, and the profile denies writes under
  the home folder. Codex exits 0 when that write fails, so the answer would be silently empty. On this machine the repo
  is in `/private/tmp`, which the profile does not deny, so this failure would not happen here. But the README says the
  eval Mac keeps the repo in `~/evals/agent-evals`, which is under the home folder. So the lane writes `-o` to scratch
  and copies it out, as the note recommends.
- **Applied: stdout and stderr redirects.** These are opened by the shell before `sandbox-exec` starts, so they already
  work. I kept them pointing into the run folder.
- **Applied: check for "Operation not permitted" in stderr.** Added as the warning line in `codex_sandboxed_run`. The
  smoke run had zero matches.
- **Applied: the smoke run as verification.** Done, see below.
- **Did not apply: `--output-dir` (Mistral Vibe).** This harness has no Mistral lane.
- **Did not reproduce: the original failure.** I did not make Codex write `-o` into a denied folder and confirm the
  silent exit 0. I wrote the fix from the profile rules and the note's report. The lane does not depend on that
  reproduction.

## Verification

- **Profile probe, `STATE=~/.codex`:** `~/.gitconfig` read denied; `~/.kimi-code` read denied; `~/.codex/config.toml`
  read allowed; a write to `~` denied (no file created); a write to `/tmp` allowed.
- **Profile probe, `STATE=~/.kimi-code` (kimi's setting):** `~/.kimi-code` read allowed; `~/.codex/config.toml`
  denied; `~/.gitconfig` denied. Kimi's access is unchanged.
- **`bash -n run.sh`:** passes.
- **Smoke run, `./run.sh fizz codex-sandboxed 1`:** exit 0, 20 s. `final.txt` is 218 bytes and `answer.json` source is
  `final.txt`. The answer says the multiple-of-3 check was moved after the multiple-of-15 check and that 15, 30 and 45
  now return `FizzBuzz`. `agent.err` has no "Operation not permitted" line. Its only errors are PostHog MCP OAuth
  messages, which are not sandbox errors. No scratch folders from this run were left in `/tmp`.
- I did not run the `kimi` lane end to end. Only its profile access was checked.

## Differences from the `codex` lane (and things to decide)

- **The sandboxed shell can read `~/.codex/auth.json`.** The profile can't keep the agent's shell from a folder that
  Codex itself must read, and copying the login into `/tmp` would be worse. This is the same tradeoff kimi makes with
  `~/.kimi-code`, but it does mean the fence does not protect the Codex login. If you want it closed, the other option
  is a `CODEX_API_KEY` in the environment with a scratch `CODEX_HOME`; this shell has no such key, so I did not switch
  to it.
- **The fix is discarded.** `run.sh` deletes the scratch workspace at the end, as it does for every lane. The run folder
  holds the answer, the logs and `meta.json`, not the edited `fizz.py`. This matches the `codex` and `kimi` lanes.
- **MCP servers from `~/.codex/config.toml` may not start inside the fence.** The `pencil` server's binary lives under
  the home folder, so the sandbox cannot read it. Its output did not appear in this run's stderr, so I cannot say whether
  it failed. The `codex` lane has no such restriction.
- **Not committed.** Changes are in the working tree only. `runs/` is gitignored, so the smoke run's folder is not
  tracked.
