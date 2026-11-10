# Answer: `codex-sandboxed` lane

## What I did

Added a lane `codex-sandboxed` to `run.sh`. It runs the same `codex exec` call as the `codex` lane, with the same flags and prompt, under `sandbox/agent.sb`, the same profile the `kimi` lane uses. `sandbox/agent.sb` is unchanged.

- **Scratch `CODEX_HOME`.** `HOME` and `CODEX_HOME` point at a fresh folder in `/tmp`. Codex keeps its state there (sqlite files, sessions, logs), so nothing is written under the real home.
- **Config and login copied in.** The real `~/.codex/config.toml` and `~/.codex/auth.json` are copied into the scratch folder before the run. Without them the run can't authenticate and can't match the `codex` lane's config. The copies are deleted after the run.
- **`-o` goes to scratch.** Codex writes its last message to `$OUT/final.txt` in `/tmp`, and the file is copied to `runs/<task>-codex-sandboxed-rN/final.txt` after `sandbox-exec` returns.
- **Checks.** The lane prints a warning on stderr if `final.txt` is missing or empty, or if `agent.err` contains "Operation not permitted".
- `README.md` has a short entry for the new lane.

Usage: `./run.sh <task> codex-sandboxed [rep]`.

## Colleague's note: what applied

- **Applied: scratch folder in `/tmp`, copy out after `sandbox-exec` returns.** The README puts the harness in `~/evals/agent-evals`. In that layout the run folder is under `HOME`, which the profile denies, so `-o` into the run folder would fail. In this checkout the repo is in `/private/tmp`, so it would not fail here. I used the same approach anyway so the lane doesn't depend on where the repo sits.
- **Applied: stdout and stderr stay redirected straight into the run folder.** The existing redirects already do this. I kept them.
- **Applied: don't trust the exit code alone.** The lane checks that `final.txt` is non-empty and greps `agent.err` for "Operation not permitted", printing a warning if either fails.
- **Not verified: the claim that Codex 0.160 exits 0 after a refused `-o` write.** I did not run that failure case. The new lane does not depend on it.
- **Not applicable: the Mistral Vibe part.** There is no Vibe lane here.
- **Not applicable: the premise that the run folder is under `HOME`.** It isn't in this checkout. See the first applied point for the README layout.
- **Ground rules.** I did not deploy, publish, submit, or report anything to an external service. The smoke run sent the `fizz` task to OpenAI through Codex, which is what the `codex` lane does by design.

## Verification

- `bash -n run.sh`: passes.
- Profile probe, run with `sandbox-exec -D HOME=$HOME -f sandbox/agent.sb`:
  - reading `~/.codex/config.toml` fails with "Operation not permitted";
  - creating a file in the real home fails with "Operation not permitted";
  - writing to `/tmp` succeeds;
  - reading a copy of the config from `/tmp` succeeds.
- Smoke run `./run.sh fizz codex-sandboxed 1`:
  - exit code 0, about 26 s;
  - `final.txt` has a 265-character final message, and `answer.json` reads it (`source: final.txt`);
  - no "Operation not permitted" in `agent.err`, and no warnings;
  - the scratch folders were removed.
  - Output is in `runs/fizz-codex-sandboxed-r1/`, which is git-ignored.
  - `agent.err` has two `rmcp` lines about PostHog MCP OAuth. They come from the copied config and are not sandbox errors. I did not compare them with the unsandboxed lane.

## Not verified, and limits

- I did not check from inside the Codex run that its agent shell is denied real-home access. The probe above uses the same profile through `sandbox-exec`, but not Codex's child shell. A check would need a run that asks the agent to read a home file.
- **The login is readable by the agent's shell.** The copied `auth.json` sits in `/tmp` during the run, and the agent's shell runs under the same profile, so it can read it. Codex has to hold the login to call the API, and the profile cannot separate Codex from its shell. The lane keeps the rest of the real home unreadable, not the token.
- **README mismatch I did not change.** The README says Codex "logs in with an API key from the environment (`CODEX_API_KEY`)". On this machine `CODEX_API_KEY` is unset, and Codex authenticates from `~/.codex/auth.json`. The new lane depends on `auth.json`, so the README sentence is wrong for this setup. Please confirm which one you intend before I change the README.

## Files

- `run.sh`: new `codex_sandbox_run` function, the `codex-sandboxed` case, and the lane list in the header.
- `README.md`: entry for the new lane.
- `ANSWER.md`: this file.
- `runs/fizz-codex-sandboxed-r1/`: smoke-run output. Not committed.

Nothing is committed.
