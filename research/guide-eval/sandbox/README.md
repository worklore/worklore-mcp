# sandbox/: an allowlist environment for the headless agents

The guide-eval harness launches coding agents headless (Claude Code `claude -p`,
Codex CLI `codex exec`, Antigravity `agy -p`) in a fresh temp dir. Up to round 8
the secrets were kept out of the child with a denylist in `round8/run.sh`:

    env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY -u PLAUSIBLE_API_KEY \
        -u DATAFORSEO_PASSWORD -u DATAFORSEO_LOGIN -u ANTHROPIC_API_KEY EVAL_NO_SECRETS=1 <agent>

A denylist removes the names someone remembered. This folder replaces it with an
allowlist: the child starts from an empty environment (`env -i`) and receives only
the names listed in `env.sh`, each with a comment saying why it is there. `verify.sh`
is launched the same way as the agent and proves, from inside the child, that nothing
else came through. Nothing in this folder prints a value; only names.

Files:

- `env.sh`: sourceable. Defines `SANDBOX_ALLOW` (names copied from the parent when
  set), `SANDBOX_SET` (values the sandbox sets itself), per-CLI extras, and the
  functions `sandbox_exec <cmd...>` (env -i + allowlist) and `sandbox_run <cmd...>`
  (runs `verify.sh` first and refuses to launch if it fails, exit 97).
- `verify.sh`: run inside the sandbox. Prints the names the child received, exits
  1 if a name is outside the allowlist, 2 if a value matches a secret shape, 3 for both.
- `README.md`: this file.

## The allowlist

Common to all three CLIs. Copied from the parent only when set there (unset ones are
skipped, so `LANG`, `LC_ALL` and `SSL_CERT_FILE` were not in the child on this machine).

| Name | Why |
|---|---|
| `HOME` | every CLI finds its login state under it: `~/.claude`, `~/.codex`, `~/Library/Application Support/Antigravity` |
| `PATH` | the CLIs are found through it; the agent's own commands need git, node, python |
| `TERM` | terminal type, so a child pager or ncurses tool does not fall back to "dumb" |
| `LANG`, `LC_ALL`, `LC_CTYPE` | locale; macOS Terminal sets `LC_CTYPE`, keeps UTF-8 for the Russian prompts |
| `TMPDIR` | macOS per-user temp dir; the CLIs and git write there |
| `SHELL` | agy runs the agent's commands in `$SHELL` (zsh), the shell that re-reads `~/.zshenv`; kept so the test matches production |
| `USER`, `LOGNAME` | looked up by git without user.name, ssh and a few tools; no secret in them |
| `SSL_CERT_FILE` | only if the parent uses a custom CA bundle; unset here |
| `EVAL_NO_SECRETS=1` | set by the sandbox. `~/.zshenv` wraps its secret exports in a guard on this name; agy's and Codex's agent shells re-read `~/.zshenv`, so without it the secrets come back from the login file even though `env -i` dropped them |

Per CLI: none. `SANDBOX_ALLOW_claude`, `SANDBOX_ALLOW_codex` and `SANDBOX_ALLOW_agy`
are empty arrays. All three CLIs started and answered on the first attempt under the
common list, so no start failed and there is no error text to report. The minimal
list was found by starting with the names the brief named and adding nothing. I did
not spend runs removing `HOME` or `PATH` to provoke a failure; the reason each name
is there is in the comment, not in an observed error.

Trial per CLI, 2026-11-01, in a fresh `mktemp -d /tmp/sb-XXXXXX`, `timeout 180`, the
exact flags of `round8/run.sh` (strict MCP config with no servers, permissions skipped,
stream-json), models `claude-haiku-5-5`, `gpt-6-sol` low, `gemini-3.8-flash-low`:

| CLI | version | "reply with the single word ok" | wall |
|---|---|---|---|
| Claude Code | 2.1.314 | `ok`, exit 0, stderr empty | 4 s |
| Codex CLI | 0.160.0 | `ok`, exit 0, stderr "Reading additional input from stdin..." (same as round 8) | 8 s |
| Antigravity agy | 1.4.8 | `ok`, status SUCCESS, exit 0, stderr empty | 9 s |

Six runs in total (one start test and one env test per CLI), none failed.

## Verification

### verify.sh, launched the same way as the agent

    . sandbox/env.sh; sandbox_exec bash sandbox/verify.sh

Result: `verify: 11 names in the child, cli=none, result=PASS (exit 0)`. The names:

    EVAL_NO_SECRETS HOME LC_CTYPE LOGNAME PATH PWD SHELL SHLVL TERM TMPDIR USER

`PWD` and `SHLVL` are added by the child's own bash, not inherited; `env.sh` lists them
with `OLDPWD` and `_` under `SANDBOX_SHELL_OWN` and `verify.sh` tolerates them.

The same script without the sandbox, in the launching shell, finds 49 names and
fails with exit 3: 38 names outside the allowlist and four values with a secret
shape: `CLAUDE_CODE_MESSAGING_TOKEN` (hex32), `GEMINI_API_KEY` (base64-40),
`PLAUSIBLE_API_KEY` (base64-40), `WORKLORE_TOKEN` (hex32 and base64-40).
`DATAFORSEO_PASSWORD` and `DATAFORSEO_LOGIN` are too short for any shape; only the
name check catches them, which is the point of an allowlist. A planted
`FAKE_AWS=AKIA...`, `FAKE_HEX` and `FAKE_B64` inside the sandbox were each flagged by
name with the right shape (self-test, exit 3).

### Through the agents themselves

Each CLI, under the allowlist, got the prompt: run `env | cut -d= -f1 | sort` and
reply with the names, one per line, no values. The reply, compared against the
allowlist plus the shell's own names:

**Claude Code (haiku 5.5), 25 names.** The 11 above (minus the two bash-only
ones, plus `_`) and 14 that Claude Code sets for its own tool shell:
`AI_AGENT CLAUDECODE CLAUDE_CODE_CHILD_SESSION CLAUDE_CODE_ENTRYPOINT
CLAUDE_CODE_EXECPATH CLAUDE_CODE_MESSAGING_SOCKET CLAUDE_CODE_MESSAGING_TOKEN
CLAUDE_CODE_SESSION_ATTENDED CLAUDE_CODE_SESSION_ID CLAUDE_EFFORT CLAUDE_PID
COREPACK_ENABLE_AUTO_PIN GIT_EDITOR NoDefaultCurrentDirectoryInExePath`.
`CLAUDE_CODE_MESSAGING_TOKEN` is a fresh per-session token the CLI mints for itself,
not the launcher's; verify.sh runs before launch and never sees it.

**Codex CLI (gpt-6-sol low), 34 names.** The allowlist, 6 Codex names
(`CODEX_CI CODEX_MANAGED_BY_NPM CODEX_MANAGED_PACKAGE_ROOT CODEX_SESSION_ID
CODEX_THREAD_ID CODEX_VERSION`), 5 terminal and pager names Codex sets
(`COLORTERM GH_PAGER GIT_PAGER NO_COLOR PAGER`), `LANG` and `LC_ALL` set by Codex,
`__CF_USER_TEXT_ENCODING` from macOS, and 7 that come from her zsh login files:
`FPATH HOMEBREW_CELLAR HOMEBREW_PREFIX HOMEBREW_REPOSITORY INFOPATH JAVA_HOME
RBENV_SHELL`. Codex runs every command as `/bin/zsh -lc`, a login shell, so
`~/.zshenv` and `~/.zprofile` are re-read inside the child. The secret exports in
`~/.zshenv` did not come back: the `EVAL_NO_SECRETS` guard held.

**Antigravity agy (gemini-3.8-flash-low), 28 names.** The allowlist, 10
`ANTIGRAVITY_*` names agy sets for its agent (`ANTIGRAVITY_AGENT
ANTIGRAVITY_AGENTAPI_EXE ANTIGRAVITY_APP_DATA_DIR ANTIGRAVITY_CONVERSATION_ID
ANTIGRAVITY_CSRF_TOKEN ANTIGRAVITY_LS_ADDRESS ANTIGRAVITY_LS_VERSION
ANTIGRAVITY_PROJECT_ID ANTIGRAVITY_SOURCE_METADATA ANTIGRAVITY_TRAJECTORY_ID`) and 6
editor and pager names (`GIT_EDITOR GIT_PAGER HGEDITOR JJ_EDITOR JJ_PAGER PAGER`).
No `FPATH` or `HOMEBREW_*`, so agy's shell is not a login shell; it re-reads
`~/.zshenv` only, and with `EVAL_NO_SECRETS=1` present the guarded names are absent.
This is the shell that printed the four secrets in rounds 1, 4, 5 and 8. Two
Antigravity `language_server` processes were running during the test (left from
earlier sessions); the agent shell still saw none of the guarded names.
`ANTIGRAVITY_CSRF_TOKEN` is agy's own session token, minted inside the child.

In none of the three reports does `WORKLORE_TOKEN`, `WORKLORE_API`, `GEMINI_API_KEY`,
`PLAUSIBLE_API_KEY`, `DATAFORSEO_PASSWORD`, `DATAFORSEO_LOGIN` or `ANTHROPIC_API_KEY`
appear. No line in any run log or stderr matched a secret shape (checked by count,
then the logs were deleted; only the name lists were kept).

## Using it in a runner

`sandbox_run` is the one-line replacement for the `E=(env -u ...)` array in
`round8/run.sh`. A future round's `run.sh`:

    . "$D/sandbox/env.sh"
    claude_run() { cd "$W" && timeout $T sandbox_run claude -p "$P" --model "$1" ...; }
    codex_run()  { cd "$W" && timeout $T sandbox_run codex exec ...; }
    agy_run()    { cd "$W" && timeout $T sandbox_run ~/.local/bin/agy ...; }

`sandbox_run` runs `verify.sh` under the same `env -i` first and prints its names to
stderr; a failure returns 97 and the agent is never started. Set `SANDBOX_CLI=claude`
(or `codex`, `agy`) to include that CLI's extra list; today all three are empty.
`round8/` itself is published data and was not changed.

## The difference from the denylist, in one paragraph

Run `verify.sh` under round 8's exact `env -u ... EVAL_NO_SECRETS=1` line from this
session's shell and the child gets 44 names, 33 of them outside the allowlist,
including `SSH_AUTH_SOCK` (the agent could sign with her ssh keys),
`CLAUDE_CODE_MESSAGING_TOKEN` (a live session token, secret-shaped),
`TERM_SESSION_ID`, `SECURITYSESSIONID` and the whole `CLAUDE_CODE_*` set. None of
those were named in the denylist because nobody thought of them; the denylist was
written for four API keys and only ever knew those. The allowlist child gets 11
names and the question "did we forget one?" has no meaning anymore: a new secret
exported tomorrow in `~/.zshrc` or by a new tool's installer never reaches the
agent, and if it somehow does, `verify.sh` fails on its name before the agent runs.

## What the allowlist does not close

An agent that runs `env -i /bin/zsh -c env` inside its own shell (Gemini did exactly
this in round 5 and round 8 while diagnosing a launchd job) drops `EVAL_NO_SECRETS`,
and the fresh zsh re-reads `~/.zshenv` with the guard off. The allowlist is about what
the launcher passes down; it cannot reach into a login file. The fix for that side is
in `~/.zshenv` itself: guard the exports on a marker file as well as the variable
(`[ ! -e ~/.eval-no-secrets ]`), since `env -i` drops any variable but not a file,
or move the exports to a file only interactive shells source. That file was not
opened or changed for this work.
