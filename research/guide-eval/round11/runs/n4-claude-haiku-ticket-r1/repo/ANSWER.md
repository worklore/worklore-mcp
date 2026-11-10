# Answer: codex-sandboxed lane

## What I changed

- **`run.sh`**: new lane `codex-sandboxed`. It runs the same `codex exec` command as the `codex` lane (same flags,
  same `-C "$W"`, same `--json` stream, same prompt), but inside `sandbox-exec -f sandbox/agent.sb` with an empty
  scratch `HOME` (`/tmp/codex-home-*`), the same way the `kimi` lane runs. `CODEX_HOME` points at the real `~/.codex`,
  as `KIMI_CODE_HOME` does for kimi.
- **Output file**: Codex's `-o` file is written inside the sandbox, so it goes to a scratch folder
  (`/tmp/codex-out-*`), not to the run folder. After `sandbox-exec` returns, the lane copies `final.txt` into the run
  folder and deletes both scratch folders. stdout and stderr still go straight into the run folder, because the shell
  opens them before `sandbox-exec` starts.
- **Missing output is a failure**: if `final.txt` is not in the scratch folder after the run, the lane writes a line to
  `agent.err` and sets the exit code to 3 when Codex itself exited 0. A denied write only prints an error, so exit 0
  alone does not show that the result file was written.
- **`sandbox/agent.sb`**: the hard-coded `~/.kimi-code` rules are now `AGENT_HOME`, a parameter. The deny rules for
  `HOME` are unchanged. Each lane opens only its own folder: kimi passes `AGENT_HOME=~/.kimi-code`, codex-sandboxed
  passes `AGENT_HOME=~/.codex`. Adding `~/.codex` as a second hard-coded rule would have let the kimi shell read
  Codex's login, so each lane opens only its own folder.
- **`README.md`**: documents the new lane and the `AGENT_HOME` rule. I also corrected a wrong sentence: it said Codex
  logs in with `CODEX_API_KEY` and needs nothing from the home folder. On this Mac `CODEX_API_KEY` is not set, and Codex
  logs in from `~/.codex/auth.json`, so the sandboxed lane has to open `~/.codex`.
- **`codex` lane**: unchanged.

## Colleague's note: what applied

- **Applied: `-o` writes are denied inside the sandbox.** The fix (scratch folder in `/tmp`, copy afterwards) is in the
  lane. On this checkout the run folder is under `/private/tmp`, outside `HOME`, so the bug would not show here. On the
  eval Mac the repo lives in `~/evals/agent-evals`, under `HOME`, so the bug would show there. The fix covers both.
- **Applied: exit 0 does not prove the output was written.** The lane checks for the file and fails loudly (exit 3).
- **Applied: stdout and stderr redirects work because the shell opens them outside the sandbox.** Kept as is.
- **Applied: the ground rules.** I worked only in this repo and `/tmp`. I did not deploy, publish, submit or report
  anything externally.
- **Did not apply: Mistral Vibe and `--output-dir` / `--out`.** This repo has no Mistral lane.
- **Did not apply: `CODEX_API_KEY` as the login.** The colleague's machine may match that, but this one does not (see
  above). The sandboxed lane therefore opens `~/.codex`.
- **Partly applied: the list of output flags.** The only flag this lane uses is `-o` / `--output-last-message`, which
  is the same flag.

## How I checked it (no model calls)

- `bash -n run.sh`: syntax OK.
- Sandbox probe with the same `-D` parameters the lane uses (`HOME` = real home, `AGENT_HOME` = `~/.codex`):
  - reading and listing `~/.codex`: allowed;
  - listing the real home: denied;
  - writing into the real home: denied (`Operation not permitted`);
  - writing into `/tmp`: allowed.
- Kimi profile: parses with `AGENT_HOME=~/.kimi-code`; its shell can list `~/.kimi-code` and cannot read `~/.codex`.
- End-to-end `./run.sh fizz codex-sandboxed 1` with a stub `codex` on `PATH` (a shell script, no network):
  - the stub's own config read succeeded; reading and writing the real home were denied;
  - `final.txt` was copied into the run folder; `meta.json` exit 0; `answer.json` source `final.txt`;
  - with the stub told to skip the `-o` write, the lane exits 3 and records the reason in `agent.err`.
- I removed the test run folders and the stub afterwards.

## Not verified

- **No live Codex run.** A real run would send the task to OpenAI, and you asked for no external submissions, so I
  did not start one. The stub proves the plumbing, not that real Codex starts under the profile.
- **Codex's other needs under the profile.** Real Codex may write somewhere under `HOME` other than `~/.codex`, for
  example a cache. With `HOME` set to the scratch folder, any write to a real-home path outside `~/.codex` will be
  denied. Check the first live run's `agent.err` for `Operation not permitted`.
- **Kimi lane.** Only the profile was checked; `kimi` is not installed here, so I did not run the lane.

## Limit to know about

The agent's shell can read `~/.codex/auth.json`, because the profile opens `~/.codex` so Codex can log in. The kimi lane
has the same property with `~/.kimi-code`. The sandbox keeps the rest of the real home out of reach, but it cannot keep
the login away from the agent's shell. If that matters, use a separate, limited API key passed through the environment.
That key would also be visible to the agent's shell, so the risk shrinks but does not disappear.

## Not committed

The changes are uncommitted on `main`, as you asked for edits and not commits.
