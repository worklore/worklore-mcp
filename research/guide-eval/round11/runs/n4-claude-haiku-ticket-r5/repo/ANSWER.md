# Answer: codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed`. It runs the same `codex exec` command as the `codex` lane (same flags and prompt), with the Codex process under `sandbox-exec -f sandbox/agent.sb`, as the kimi lane does. Its shell therefore cannot read or write the real home. The lane:
  1. Makes a scratch `CODEX_HOME` in `/tmp` and copies `auth.json` and `config.toml` into it from the real `~/.codex`. The copy happens before the sandbox starts.
  2. Runs codex with `HOME` and `CODEX_HOME` pointing at the scratch folder, and `-D HOME=<real home>` for the profile.
  3. Passes `-o "$OUT/final.txt"`, where `OUT` is a scratch folder in `/tmp`. After the run it copies that file to `runs/<task>-codex-sandboxed-rN/final.txt`, then deletes the scratch folders.
  4. If codex exits 0 but the last-message file does not exist, it writes a line to `agent.err` and sets the exit code to 1, so the grader does not see a silent success.
- **`README.md`**: added the new lane to the lane list. I also corrected a paragraph that said Codex needs nothing from the home folder. That was wrong for this machine (see below).
- **`ANSWER.md`**: this file.

## Which parts of the colleague's note applied

- **Applied: the output-file write.** Codex's `-o` write runs inside the sandbox, and the profile denies writes under the real home. So the lane writes to a `/tmp` scratch folder, copies afterwards, and checks that the file exists instead of trusting exit 0. The note's fix is the one I used.
- **Applied: stdout and stderr stay in the run folder.** The shell opens those redirects before `sandbox-exec` starts, so they work. The new lane keeps them as they were.
- **Applied, with a caveat: the run-folder location.** In this checkout the repo is at `/private/tmp/h-nt2IbQ`, which is outside `$HOME`, so the `-o` write would succeed here even without the scratch folder. The README says the harness lives in `~/evals/agent-evals` on the eval Mac, which is under the home folder. So the scratch-folder design is needed there, and I kept it.
- **Not applied: the Mistral Vibe lane and its `--output-dir` flag.** This repo has no Vibe lane, so I did not touch one.
- **Not applied as written: "scratch HOME, nothing else from home".** The colleague's setup did not need anything from the home folder. Here it does. `CODEX_API_KEY` is not set on this machine, and the `codex` lane authenticates from `~/.codex/auth.json`. The sandboxed lane therefore has to be given that login. I seed the scratch `CODEX_HOME` with copies of `auth.json` and `config.toml`.

## Trade-offs and differences from the `codex` lane

- **Credentials are visible to the agent's shell.** The sandbox applies to the whole process tree, and codex needs the login to call the API. So the agent's shell can read the copied `auth.json` in `/tmp`. The kimi lane has the same property for `~/.kimi-code`. The copy is deleted when the lane finishes. If you want the agent's shell to be unable to read the login at all, the lane needs a different authentication path, such as an API key in the environment.
- **MCP servers and plugins in `config.toml` may not start.** The config refers to a binary under the real home (`~/.pencil/...`). The sandbox blocks reads there, so that MCP server will fail inside this lane. The unsandboxed `codex` lane does not have this problem, so the two lanes are not identical in tools. I did not edit the copied config.
- **The Codex shell is not sandboxed by Codex.** The lane keeps `--dangerously-bypass-approvals-and-sandbox` to match the `codex` lane. So the outer profile is the only fence.
- **Network stays open.** The profile is `(allow default)` with specific denies. That is the same as the kimi lane. The task reaches the model provider by design.
- **The exit-code change is limited to this lane.** The `codex` lane is unchanged.

## What I verified

- `bash -n run.sh` passes.
- Under `sandbox/agent.sb` with `-D HOME=<real home>`:
  - reading the real `~/.codex/config.toml` is denied (`Operation not permitted`);
  - writing into the real `~/.codex` is denied;
  - reading and writing in a `/tmp` scratch folder works;
  - `codex login status` with the scratch `CODEX_HOME` reports "Logged in using ChatGPT", so the copied login works in the sandbox.
- Lane plumbing, run with a fake `codex` on `PATH` (no model call):
  - Case A: the fake wrote the `-o` file. The lane produced `final.txt`, `agent.log`, `meta.json`, and `answer.json` with the expected content. Its attempted write and read of the real home were both denied, and the scratch folders were removed.
  - Case B: the fake exited 0 without writing the `-o` file. The lane recorded the error in `agent.err` and set `exit_code` to 1.
  - I removed the test run folders and the fake `codex` afterwards.

## Not verified

- **No live Codex run.** A real `codex-sandboxed` run sends the fizz task to the model provider, and you did not ask me to run it. I did not run it. The sandbox and auth checks above cover the parts that can fail before the model call. The `-o` write under the real sandbox with a live codex is not directly tested. The first live run should confirm that `final.txt` is non-empty and that `agent.err` has no "last message" error.
- **The original `-o` failure was not reproduced here.** It depends on the run folder being under the home folder, and this checkout is not.

## Suggested next step

Run `./run.sh fizz codex-sandboxed 1` once on the eval Mac, where the harness lives under the home folder. Check that `final.txt` is present and non-empty, and that `agent.log` has the event stream. Then compare the answer with the `codex` lane's answer.
