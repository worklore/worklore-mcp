# Answer: codex-sandboxed lane

## What I changed

**`run.sh`** gets a `codex-sandboxed` lane. It runs the same `codex exec` command as the `codex` lane (same flags, same
`-C`, same `--json`, same `< /dev/null` and stdout/stderr redirects into the run folder), but:

- the Codex process runs under `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb`, as the kimi lane does;
- `HOME` is an empty scratch folder in `/tmp` and `CODEX_HOME` points inside it, so Codex doesn't read `~/.codex`;
- `-o` writes to a scratch folder in `/tmp`. After `sandbox-exec` returns, the lane copies `final.txt` into the run
  folder and deletes the scratch folders;
- if no `final.txt` ends up in the run folder, the lane sets the exit code to 1 (or keeps a non-zero code) and writes a
  line to `agent.err`. It also prints a warning if `agent.err` contains "Operation not permitted";
- it exits with code 2 before starting if `CODEX_API_KEY` is unset.

The lane is also listed in the `run.sh` header comment and in `README.md`.

**`sandbox/agent.sb` is unchanged.** Its existing rules already cover this lane: they deny reads and writes under the real
home and allow `/tmp`.

**`README.md`** has a bullet for the new lane.

## Which parts of the colleague's note applied

- **Applied: output files inside a denied folder.** I checked this directly. Under the profile, a write into a folder
  under the real home fails with `Operation not permitted`, and a write under `/tmp` works. The README says the harness
  lives in `~/evals/agent-evals` on the eval Mac, so on that machine `-o "$R/final.txt"` would be denied. That is the
  same failure the note describes. The fix is the note's: scratch in `/tmp`, copy out after the sandbox exits.
- **Applied: don't trust the exit code alone.** Codex exits 0 when it can't write its output, so the lane checks for
  `final.txt` and does not pass a run without it.
- **Applied: stdout and stderr redirects are fine.** The shell opens them before `sandbox-exec` starts, so the logs stay
  in the run folder.
- **Did not apply: Mistral Vibe and `--output-dir`.** This repo has no Mistral lane.
- **Did not apply: the Codex 0.160 specifics.** The lane uses `-o` as the `codex` lane already does. I did not check the
  note's exact error text against this Codex version, because I did not run a live Codex job.
- **Not done: the note's smoke run.** I did not run a live job, so the note's verify step is still open; see "Not verified" below.

## Decisions you may want to change

- **Login comes from `CODEX_API_KEY`, not `~/.codex/auth.json`.** The README already says Codex logs in from that
  variable. Here `CODEX_API_KEY` is not set, and `~/.codex/auth.json` holds the login. I did not copy `auth.json` into
  `/tmp` or open it in the profile. The sandboxed shell has network access, so either would let the agent read the
  credentials and send them out. If you want this lane to run without an API key, that needs a decision from you.
- **The sandboxed Codex does not get `~/.codex/config.toml`.** That file holds MCP servers, plugins, and trust entries
  for project paths. I checked its key names with values redacted. I saw no top-level `model` or `model_provider`
  lines, but I did not read the whole file. The sandboxed run therefore uses Codex's defaults, not those settings. If
  the two lanes should differ only in the sandbox, copy the non-secret settings into the scratch `CODEX_HOME`.
- **The sandboxed Codex runs with `--dangerously-bypass-approvals-and-sandbox`**, the same as the `codex` lane. The
  outer `sandbox-exec` is the fence. Codex's own sandbox would likely not nest inside it.

## What I verified

1. **The profile denies writes under the real home.** I created a folder in `~` outside the sandbox, then wrote into it
   from inside `sandbox-exec`. The write failed with `Operation not permitted`.
2. **The profile denies reads of `~/.codex/auth.json`.** A `cat` from inside the sandbox failed with `Operation not
   permitted`.
3. **The profile allows writes under `/tmp`.** A write there succeeded.
4. **Lane plumbing, with a stub `codex` on `PATH`** (the stub is not the real Codex; it is in `/tmp` and I removed it):
   - Normal case: `final.txt` was copied into the run folder, `answer.json` read it (`source: final.txt`), and the exit
     code was 0. The stub's `auth.json` read was denied inside the sandbox, and `CODEX_HOME` pointed at the scratch
     folder.
   - No `CODEX_API_KEY`: the lane exited with code 2 and a clear message.
   - Stub exits 0 without writing its output file: the lane recorded exit 1 and wrote a line to `agent.err`.
   - Test runs were removed from `runs/`. `bash -n run.sh` passes.

## Not verified

- **A live `codex exec` run in the sandbox.** I have no `CODEX_API_KEY` in this shell, and a real run sends the task to
  the model provider, so I did not start one. The first real check is `./run.sh fizz codex-sandboxed 1` with the key
  set. Look for: a non-empty `final.txt`, `answer.json` with `source: final.txt`, and no "Operation not permitted" in
  `agent.err`. Codex itself may need something from the real home that the profile blocks. The stub test does not
  show that. If it does, the fix is to allow that specific path, not to open the whole home.
- **Whether `answer.json` is graded.** `check_answer.py` falls back to the event stream only for `kimi*` lanes. The new
  lane reads `final.txt` only, so an empty `final.txt` gives `source: none`. I left the grader alone.
- **The leftover `/tmp/chome-*` folders.** Three from earlier today, from before my tests, are still in `/tmp`. I left
  them alone.
