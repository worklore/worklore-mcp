# ANSWER: codex-sandboxed lane

## What I changed

- `run.sh`: new lane `codex-sandboxed`, the same `codex exec` call as the `codex` lane, run as
  `sandbox-exec -D HOME=<real home> -f sandbox/agent.sb` the way the `kimi` lane does it.
  - Scratch HOME and CODEX_HOME in `/tmp` (`mktemp -d /tmp/chome-XXXXXX`), with `.codex/` created so Codex does not warn that it is missing.
  - `-o` points at a scratch folder in `/tmp` (`/tmp/cout-XXXXXX/final.txt`), not at the run folder.
  - After `sandbox-exec` returns, the lane copies `final.txt` into the run folder if it exists and is non-empty. If not, it appends a line to `agent.err`. Exit code 0 alone does not establish that the file was written.
  - stdout and stderr stay redirected straight into the run folder, since the shell opens them outside the sandbox.
  - Both scratch folders are removed at the end.
  - The header comment lists the new lane.
- `README.md`: one entry for the new lane.
- `ANSWER.md`: this file.

Nothing was committed.

## Colleague's note: what applied

- **Applied: `-o` into the run folder fails under the profile.** I reproduced it in this environment. A write under the real home is denied by the profile, and `sandbox-exec` returns `Operation not permitted`. This is why `-o` goes to `/tmp`. The fix is the scratch-folder-then-copy pattern the note describes.
- **Applied: exit 0 does not prove the result was written.** The lane checks for the file after the run and records a warning in `agent.err` when it is missing. `check_answer.py` already handles an absent `final.txt` by reporting `source: none`.
- **Applied: stdout and stderr stay in the run folder.** They are opened by the shell before `sandbox-exec` starts, and they worked in my probe.
- **Did not apply: the Mistral Vibe `--output-dir` case.** There is no Vibe lane in this repo.
- **Did not apply as stated: "the run folder is under the real home."** In this checkout the repo is at `/private/tmp/h-7TRiS3`, outside the home folder, so the bug would not show here. The README says the eval Mac uses `~/evals/agent-evals`, which is under the home folder, so the scratch-folder fix is still needed there. I checked the failure with a probe directory under the real home, then removed it.

## Verification

- Sandbox behavior, run directly with `sandbox-exec` and `sandbox/agent.sb`:
  - a read of the real `~/.codex/config.toml` is denied (`Operation not permitted`);
  - a write under the real home is denied;
  - a write under a `/tmp` scratch folder succeeds;
  - `codex --version` runs under the profile with a scratch HOME.
- Lane mechanics: I ran `./run.sh fizz codex-sandboxed 1` with a stand-in `codex` script on PATH. The stand-in:
  - reported the scratch HOME and CODEX_HOME;
  - showed the real-home read was denied;
  - wrote its last message to the `-o` path.
  The run folder got `final.txt`, `answer.json` reported `source: final.txt`, and the scratch folders were removed.
- Missing-output path: a stand-in that exits 0 without writing `-o` leaves `final.txt` absent, and `agent.err` gets the warning. `answer.json` reports `source: none`.
- `bash -n run.sh` passes.
- **Not verified:** a live run of the real `codex` lane. I did not run it, because it would send the task to an outside model provider, which the ground rules rule out. The stand-in tests cover the lane's mechanics; they do not show how real Codex behaves under the profile.

## Differences from the `codex` lane

- Codex does not see the real `~/.codex` (`config.toml`, `auth.json`). The sandboxed lane therefore uses Codex defaults plus the API key from the environment, as the README describes for the `codex` lane. If the real `config.toml` sets a model or other options, the two lanes may not be identical. Check this on the eval Mac before comparing results.
- Codex's session files go to the scratch CODEX_HOME and are deleted with it. The `kimi` lane keeps its sessions because `~/.kimi-code` is open to the profile. The sandboxed Codex lane cannot open `~/.codex` without allowing reads of the real home, which is what the lane is meant to prevent.
- The Codex binary and its node runtime are under `/opt/homebrew`, outside the home folder, so the profile needed no change. If the eval Mac has Codex or node installed under the home folder (for example via nvm), the sandbox will block them, and the profile will need an allow rule for that path.
- `--dangerously-bypass-approvals-and-sandbox` is kept, as in the `codex` lane. This skips Codex's own sandbox, so the only fence is `sandbox/agent.sb`.
