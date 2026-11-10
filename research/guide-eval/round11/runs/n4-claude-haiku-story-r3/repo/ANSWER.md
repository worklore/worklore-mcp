# Answer: `codex-sandboxed` lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed`, run as `./run.sh <task> codex-sandboxed [rep]`.
  - It runs the same `codex exec` command as the `codex` lane (same flags, same `-C`, same `--json`, same `timeout`), wrapped in `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, the same way the `kimi` lane is wrapped.
  - It uses a scratch HOME in `/tmp` and a scratch `CODEX_HOME`. Before the sandbox starts, it copies `auth.json` and `config.toml` from the real `~/.codex` into the scratch `CODEX_HOME`.
  - `-o` points at a scratch file in `/tmp`, not at the run folder. After `sandbox-exec` returns, the lane copies `final.txt` into the run folder if Codex wrote it, then deletes the scratch folder.
  - `agent.log` and `agent.err` are still redirected straight into the run folder, so the shell opens them outside the sandbox.
  - If `agent.err` has `Operation not permitted`, or no `final.txt` was written, the lane prints a warning. It does not change the exit code.
- **`README.md`**: documented the new lane.
- **`sandbox/agent.sb`**: not changed. The new lane needs nothing beyond what the profile already allows.

## Colleague's note: what applied

- **Applied: Codex `-o` into a denied folder.** The note's central failure is that `codex exec -o` into a folder the profile denies fails with `Operation not permitted`, and Codex still exits 0. The README puts the repo at `~/evals/agent-evals`, so the run folder is under the real home, and the denial would happen. The fix is the note's: write `-o` into `/tmp` and copy the file out after the sandbox exits. I use this route for every run, not only when the run folder is under home, so the lane doesn't depend on where the repo sits. In this checkout the repo is at `/private/tmp/h-SCMx4f`, which is not under home, so the deny would not trigger here.
- **Applied: don't trust the exit code alone.** The lane checks for the copied `final.txt` and for `Operation not permitted` in `agent.err`, and warns on either.
- **Applied: stdout and stderr redirects stay outside the sandbox.** This was already how both lanes worked, and the new lane keeps it.
- **Did not apply: Mistral Vibe `--output-dir`.** This harness has no Mistral lane.
- **Did not apply as written: "one smoke run per lane" with the grader.** I did not run the real `codex` lane, because that sends the `fizz` task and code to OpenAI, and the ground rules say not to send anything to an external service. The verification is below.

## Where the README was wrong

`README.md` says Codex "logs in with an API key from the environment (`CODEX_API_KEY`), so it needs nothing from the home folder." On this machine that is not true:

- `CODEX_API_KEY` is not set in my shell.
- `~/.codex/auth.json` exists and is used for login.
- `~/.codex/config.toml` exists (about 137 KB).

So an empty scratch `CODEX_HOME` would leave Codex logged out. That is why the lane copies those two files in. I did not read their contents.

## Decision for you: the login copy

Copying `auth.json` into the scratch folder puts the login token inside the sandbox. The sandboxed shell could read it, and network access stays open, so a prompt-injected run could in principle send it out. The kimi lane has the same kind of exposure, because it opens `~/.kimi-code` in full. But it is a choice you should make, not me.

Options:

1. Keep the copy (current behavior).
2. Use `CODEX_API_KEY` only. Export it, and drop the two `cp` lines. This keeps the token off disk inside the sandbox, but it needs a key on the eval Mac, and then `config.toml` is not picked up.

## Verification

Done, without any network call:

- `bash -n run.sh`: syntax ok.
- Full lane run with a stub `codex` first on `PATH` (`PATH=<stub>:$PATH ./run.sh fizz codex-sandboxed 99`):
  - The stub saw `auth.json` in the scratch `CODEX_HOME`.
  - It wrote `-o` to the scratch folder, and `final.txt` was copied to the run folder. `answer.json` read it (`source: final.txt`).
  - No `hcodex-*` scratch folder was left behind.
- Real-home denial: a write to `~/.sbprobe-lane-test` from inside the lane was denied, `Operation not permitted`. The lane printed its warning. The probe file was not created.
- The real `codex` binary (0.160.0) starts under `sandbox/agent.sb` with the scratch HOME: `codex --version` prints `codex-cli 0.160.0` and exits 0.

Not verified:

- **The real codex run.** I have not run `./run.sh fizz codex-sandboxed` against OpenAI. The stub covers the lane's plumbing, not Codex's behavior. I also have not reproduced the colleague's finding that Codex exits 0 after a denied `-o` write. Your smoke run will settle both.
- **Whether Codex needs anything else from home** during a real run, such as paths listed in `config.toml`.

Test leftovers, all removed: the `runs/fizz-codex-sandboxed-r99` folder, the stub, and the probe file. `runs/` is gitignored.

Nothing is committed.

## Next step

Run `./run.sh fizz codex-sandboxed 1` once. Expect `final.txt` to be non-empty and `agent.err` to have no `Operation not permitted` line. Then choose option 1 or 2 above.
