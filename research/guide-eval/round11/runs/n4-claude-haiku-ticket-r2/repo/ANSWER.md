# codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed` (`codex_sandboxed_run`). It runs the same
  `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json` command as the
  `codex` lane, but inside `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, with `HOME` set to an empty
  scratch folder, the same way the `kimi` lane does it.
- **`README.md`**: lane list updated.
- Nothing else changed. The `codex` and `kimi` lanes are untouched, and `sandbox/agent.sb` is unchanged.

## How the lane works

1. Creates two scratch folders in `/tmp`: `$SH` (scratch HOME and `CODEX_HOME`) and `$SCR` (for Codex's output).
2. Copies `~/.codex/auth.json` into `$SH/.codex/`. This is the only file from the real home that Codex receives.
3. Runs Codex under the sandbox with `-o "$SCR/final.txt"`. Stdout and stderr still go straight into the run folder,
   opened by the shell before `sandbox-exec` starts.
4. After Codex exits, copies `$SCR/final.txt` into `runs/<task>-codex-sandboxed-r<rep>/final.txt`. If the file is
   missing, it appends a line to `agent.err`, because Codex exits 0 even when the `-o` write fails.
5. Deletes both scratch folders.

## Colleague's note: which parts applied

- **Applied: the `-o` write problem.** The colleague's failure needs the output file to be under a denied path, which
  is the case when the run folder is inside the real home. In this repo the run folder is `runs/` under
  `/private/tmp/h-TodAOK`, and the profile only denies `$HOME`, so the write would probably have worked here. I
  used the scratch-folder pattern anyway, because the run folder could move under the home folder later and the
  pattern costs nothing. I did not reproduce the failure with a live run, so this part is untested.
- **Applied: exit 0 does not prove the result was written.** The lane checks for `final.txt` and records a
  missing file in `agent.err`.
- **Applied: keep stdout and stderr redirects in the run folder.** The shell opens them outside the sandbox.
- **Did not apply: `mktemp -d` scratch for Mistral Vibe `--output-dir`, `--out`, and similar.** This repo has no
  Mistral Vibe lane, so there was nothing to change.
- **Not in the colleague's note, but relevant:** Codex's own sandbox is turned off with
  `--dangerously-bypass-approvals-and-sandbox`, the same as the `codex` lane. The outer `sandbox-exec` is the only
  fence for the `codex-sandboxed` lane, and nesting Codex's own sandbox inside it is not something I tested.

## Verification

- `bash -n run.sh`: syntax OK.
- Under the same profile with `HOME` set to a scratch folder, `codex --version` runs (codex-cli 0.160.0).
  Reading `~/.codex/config.toml` is denied. Writing to a scratch file in `/tmp` works. These checks ran only the
  sandbox and the CLI version command. They did not start a model session.
- **Not run:** a full `./run.sh <task> codex-sandboxed`. A live run sends the task to OpenAI and uses your quota,
  and you did not ask for a run. Run it when you want to check the end-to-end result.

## Known gaps and differences from the `codex` lane

1. **The login token is readable by the agent's shell.** Codex logs in through `~/.codex/auth.json`, not an env
   key (the README says otherwise, and `CODEX_API_KEY` is not set here). Codex needs the token, so the copy in
   `$SH` is readable by the sandboxed shell for the length of the run. The profile keeps the rest of the real home
   out of reach, but not this token. The `kimi` lane has the same kind of exposure to its own credentials. If the
   token must stay out of the shell, the fix is an API-key env var or a narrower profile rule. Neither is in place.
2. **The config is not copied.** `~/.codex/config.toml` is not copied, because it holds MCP server commands and
   trust entries that could contain secrets. As a result, this lane runs Codex with default config, and the `codex`
   lane runs with your config. If model or MCP settings change results, the two lanes will not match.
3. **Token refreshes are lost.** If Codex refreshes `auth.json` during a run, the refreshed copy is deleted with the
   scratch folder, and the real file is not updated.

## Next step

`./run.sh <task> codex-sandboxed` on a small task, then check that `final.txt` is non-empty, that `agent.err` has no
"no last message" line, and that the agent's shell cannot read `~/.codex/config.toml`.
