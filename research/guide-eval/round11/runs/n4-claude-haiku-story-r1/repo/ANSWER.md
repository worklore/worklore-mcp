# codex-sandboxed lane

## What I did

- **`run.sh`**: added a `codex-sandboxed` lane. It runs the same `codex exec` call as the `codex` lane (same flags, same `-C`, `--json`, `timeout`), wrapped the way the `kimi` lane wraps Kimi:
  - `sandbox-exec -D HOME="$REAL" -f sandbox/agent.sb`, with `HOME` set to an empty scratch folder in `/tmp`;
  - `CODEX_HOME` set to an empty `.codex` inside that scratch HOME, so Codex never reads the real `~/.codex`.
- **`-o` output**: Codex writes `final.txt` to a scratch folder in `/tmp`, not to the run folder. After `sandbox-exec` returns, the lane copies `final.txt` into the run folder and deletes the scratch folders.
  - If Codex exits 0 but writes no final message, the lane sets the exit code to 3 and prints a message to stderr.
  - If Codex exits non-zero, that code is kept.
- **Guard**: the lane exits 2 at once, before running, if `CODEX_API_KEY` is unset. The reason is in the next section.
- **`README.md`**: documented the new lane.
- **`agent.sb` and the `kimi` lane are unchanged.**

## Why the auth guard exists

`~/.codex/auth.json` on this machine holds ChatGPT OAuth tokens (`tokens.access_token`, `refresh_token`, etc.). There is no `OPENAI_API_KEY` field, and `CODEX_API_KEY` is not set in this environment. The real `~/.codex` is hidden from the lane, so the lane cannot log in without a key. I did not:

- open `~/.codex` in `agent.sb`: the profile is shared with the kimi lane, so kimi's shell would then be able to read Codex's tokens;
- copy `auth.json` into the scratch HOME: a copy can be used by the agent's shell, and if the refresh token rotates, the real login used by the `codex` lane could stop working. I have not verified whether this token rotates.

**Decision needed:** set `CODEX_API_KEY` for the lane, or choose a separate profile that opens only `~/.codex` for codex runs. I did not pick between these for you.

## Colleague note: what applied

Applied:
- **Output file under a denied path.** `codex exec -o` is the only output flag in the Codex lanes. Under `agent.sb`, writes to the real HOME are denied. I confirmed this with a probe: writing `$HOME/...` inside the sandbox fails with `Operation not permitted`, while writing under `/tmp` works.
- **Fix: scratch folder, then copy.** The lane writes to a scratch folder in `/tmp` and copies `final.txt` out after `sandbox-exec` returns. This is the note's fix.
- **stdout and stderr stay redirected into the run folder.** The outer shell opens those files, so the redirects still work inside the lane, as the note says.
- **Don't trust the exit code alone.** The lane checks that a final message exists and turns a silent exit 0 without one into exit code 3.

Applied in part:
- **Verify step.** I ran a stub-based check, not a real smoke run (see below).
- **Layout.** In this checkout the run folder is `/private/tmp/h-Xfq5MB/runs`, outside HOME, so the denial would not occur here. The README describes the eval Mac layout, `~/evals/agent-evals`, which is under HOME, where it would occur. The scratch-folder design works in both layouts.

Did not apply:
- **Mistral Vibe (`--output-dir`).** No Vibe lane exists in this repo.
- **Standing `grep "Operation not permitted" runs/*/agent.err` check.** I did not add a permanent check. The sandbox also prints this line for denials the agent itself triggers, so grepping for it would give false alarms. The lane's exit-code check covers the missing-output case.
- **Grader.** `check_answer.py` is unchanged. It reads `final.txt` for any lane that is not kimi, so the new lane is graded from `final.txt` like the `codex` lane.

Ground rules followed: I did not deploy, publish, submit, or report anything externally. I did not commit.

## Verification

Done, with no model calls:
- `bash -n run.sh` passes.
- The sandbox probe above: writes under the real HOME are denied, writes under `/tmp` are allowed, and `codex --version` runs inside the profile with a scratch `CODEX_HOME`.
- **Stub run with `CODEX_API_KEY` set** (stub `codex` on `PATH`): the `-o` file was written to scratch and copied to `runs/fizz-codex-sandboxed-r2/final.txt`, with exit 0. A probe write to the real home was denied inside the stub. `answer.json` read the copied answer (13 chars).
- **Stub run with no output**: exit code 3 and the stderr message.
- **Guard**: without `CODEX_API_KEY`, the lane exits 2 before running anything.
- The test run folders were removed.

Not done:
- **A real `codex-sandboxed` run against OpenAI.** It needs `CODEX_API_KEY`, and I did not want to send the task to a provider without your go-ahead. Run `CODEX_API_KEY=... ./run.sh fizz codex-sandboxed 1` once to confirm the end-to-end result.

## Things I noticed

- `README.md` says Codex "logs in with an API key from the environment ... so it needs nothing from the home folder." On this machine, the `codex` lane's login is the OAuth file in `~/.codex`, and `CODEX_API_KEY` is not set. I left that paragraph as it was. Please check which is true on the eval Mac.
- `/tmp/khome-pDmh8P` was already there before my test runs (created 22:09, before the repo files). I did not touch it.
