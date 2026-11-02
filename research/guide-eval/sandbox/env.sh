#!/usr/bin/env bash
# sandbox/env.sh: an ALLOWLIST environment for launching coding agents headless.
#
#   . sandbox/env.sh
#   sandbox_exec claude -p "..."       # env -i + the allowlist, nothing else
#   sandbox_run  codex exec "..."      # same, but verify.sh runs first and a failure aborts
#   SANDBOX_CLI=agy sandbox_run agy ...# adds the per-CLI extras (none were needed, see README)
#
# Replaces the denylist in round8/run.sh:
#   env -u WORKLORE_TOKEN -u WORKLORE_API -u GEMINI_API_KEY ... EVAL_NO_SECRETS=1 <agent>
# A denylist removes the names someone remembered. This file starts from an empty
# environment (env -i) and copies in only the names below, each with its reason.
#
# This file never prints a value. Nothing in it writes to stdout except names.

# Names copied from the parent shell when they are set there (unset ones are skipped).
SANDBOX_ALLOW=(
  HOME           # every CLI finds its login state under it: ~/.claude, ~/.codex,
                 # ~/Library/Application Support/Antigravity; without it they log out
  PATH           # the CLIs are found through it, and the agent's own commands need git,
                 # node, python; the agent sees the same PATH you have
  TERM           # terminal type; the CLIs print nothing fancy with stream-json, kept so a
                 # child pager or ncurses tool does not fall back to "dumb"
  LANG           # locale for the child; keeps UTF-8 output (prompts here are Russian too)
  LC_ALL         # same; copied only when the parent has it set
  LC_CTYPE       # macOS Terminal sets this one instead of LANG; needed for UTF-8 in zsh
  TMPDIR         # macOS per-user temp dir (/var/folders/...); CLIs and git write there
  SHELL          # agy runs the agent's commands in $SHELL (zsh here), which is exactly the
                 # shell that re-reads ~/.zshenv; keep it so the test matches production
  USER           # a few tools (git without user.name, ssh) look it up; harmless, no secret
  LOGNAME        # same as USER on macOS
  SSL_CERT_FILE  # only if the parent uses a custom CA bundle (corporate proxy); unset here
)

# Values the sandbox sets itself, NAME=VALUE.
SANDBOX_SET=(
  EVAL_NO_SECRETS=1  # ~/.zshenv wraps its secret exports in a guard on this name. agy's
                     # agent shell re-reads ~/.zshenv, so without this the secrets come back
                     # from the login file even though env -i dropped them (seen in rounds
                     # 1, 4, 5 and 8). Keep it in every launch.
)

# Per-CLI extras, found by trial (see README). Empty means the common list was enough.
SANDBOX_ALLOW_claude=()
SANDBOX_ALLOW_codex=()
SANDBOX_ALLOW_agy=()

# Names the child's bash adds on its own when it starts (not inherited). verify.sh tolerates
# them because they appear in any `bash -c env` under env -i.
SANDBOX_SHELL_OWN=(PWD OLDPWD SHLVL _)

# sandbox_build: fills SANDBOX_ENV with `env -i NAME=value ...` for the allowed names that
# are set in the parent. Values go straight from one variable into the array; nothing is echoed.
sandbox_build() {
  local n extra
  SANDBOX_ENV=(env -i)
  for n in "${SANDBOX_ALLOW[@]}"; do
    [ -n "${!n:-}" ] && SANDBOX_ENV+=("$n=${!n}")
  done
  if [ -n "${SANDBOX_CLI:-}" ]; then
    extra="SANDBOX_ALLOW_${SANDBOX_CLI}[@]"
    for n in "${!extra}"; do
      [ -n "${!n:-}" ] && SANDBOX_ENV+=("$n=${!n}")
    done
  fi
  SANDBOX_ENV+=("${SANDBOX_SET[@]}")
}

# sandbox_names: the names the child is allowed to have, one per line (for verify.sh).
sandbox_names() {
  local n extra
  printf '%s\n' "${SANDBOX_ALLOW[@]}" "${SANDBOX_SHELL_OWN[@]}"
  for n in "${SANDBOX_SET[@]}"; do printf '%s\n' "${n%%=*}"; done
  if [ -n "${SANDBOX_CLI:-}" ]; then
    extra="SANDBOX_ALLOW_${SANDBOX_CLI}[@]"
    printf '%s\n' "${!extra}"
  fi
}

# sandbox_exec <cmd...>: run the command with only the allowlist.
sandbox_exec() {
  sandbox_build
  "${SANDBOX_ENV[@]}" "$@"
}

# sandbox_run <cmd...>: verify first, launched the same way as the command; abort on failure.
sandbox_run() {
  local d
  d="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  sandbox_exec bash "$d/verify.sh" "${SANDBOX_CLI:-}" >&2 || { echo "sandbox: verify failed, not launching: $1" >&2; return 97; }
  sandbox_exec "$@"
}
