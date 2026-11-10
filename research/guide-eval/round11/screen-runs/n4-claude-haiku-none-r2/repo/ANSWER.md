# codex-sandboxed lane

## What changed

- **`run.sh`**: new lane `codex-sandboxed`. It runs the same `codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C <work> --json -o final.txt <prompt>` command as the `codex` lane, but wrapped in `sandbox-exec -f sandbox/agent.sb` with `HOME` and `CODEX_HOME` pointing at an empty scratch dir under `/tmp`, which is removed afterwards. The kimi lane gets the same treatment, unchanged in behavior.
- **`sandbox/agent.sb`**: the profile previously had a hard-coded exception that re-opened `~/.kimi-code` for every lane that used it. I checked: under that profile, a shell could list `~/.kimi-code`, so reusing the profile unchanged would have left part of the real home readable to the codex lane. The exception is now a parameter, `(param "OPEN")`. Kimi passes `OPEN=$REAL/.kimi-code`; codex passes its scratch dir, so it opens nothing under the real home.
- **`README.md`**: documents the new lane and the `OPEN` parameter.

## Verification (local only)

- `bash -n run.sh` passes.
- `./run.sh fizz codex-sandboxed` with no `CODEX_API_KEY` exits 2 with a clear message and leaves no work dir behind.
- Probes under the profile with `OPEN` set to the scratch dir (codex lane): contents of `~/.codex/auth.json` are unreadable, `~/.codex` cannot be listed, and writes to `~/.codex` fail with "Operation not permitted". `~/.kimi-code` is also unreadable.
- Probe with `OPEN=~/.kimi-code` (kimi lane): `~/.kimi-code/bin` is listable, and `~/.codex` is blocked.
- `codex` 0.160.0 starts under the profile with a scratch `CODEX_HOME` and no sandbox errors. `codex login status` reports "Not logged in", as expected for that check.

## What I did not verify

- **No full codex run.** I did not run a real task through `codex exec`, because that sends the prompt to OpenAI and needs a key. So the end-to-end path is untested.
- **Auth is the blocker on this Mac.** The codex CLI here logs in with a ChatGPT login in `~/.codex/auth.json`, and no `CODEX_API_KEY` is set. The sandboxed codex process cannot read that file, and Seatbelt cannot tell codex's own reads from its shell's, so the lane cannot use it. The lane therefore takes the key from `CODEX_API_KEY` (the README's documented design). Until that variable is set, the lane refuses to run. I have not confirmed that `codex exec` accepts `CODEX_API_KEY` on this CLI version. If the key is set but exec still fails, that is the first thing to check.
- **Copying `auth.json` into the scratch dir** would have made the lane runnable with the current login, but it hands the shell the credential itself. I did not do that.

## Differences from the `codex` lane

- The real `~/.codex/config.toml` is not loaded, so its MCP servers (`pencil`) and plugins (`github`, `posthog`) are absent. The config sets no model, so both lanes use codex's default model.
- Auth comes from `CODEX_API_KEY`, not the ChatGPT login.
- Network stays open, as in the kimi lane.

## Not done

- Nothing committed, deployed, published or sent to any external service.
- No `runs/` output was produced; the test run directories were removed.
