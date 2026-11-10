#!/usr/bin/env bash
# usage: run.sh <task> <lane> [rep]
# lanes: codex           Codex CLI, unsandboxed
#        codex-sandboxed Codex CLI under sandbox/agent.sb (no reading or writing the real home), scratch HOME, key from $CODEX_API_KEY
#        kimi            Kimi Code under sandbox/agent.sb (no reading or writing the real home), scratch HOME
set -u
D="$(cd "$(dirname "$0")" && pwd)"
T=$1; A=$2; REP=${3:-1}
R="$D/runs/$T-$A-r$REP"; rm -rf "$R"; mkdir -p "$R"
W=$(mktemp -d /tmp/h-XXXXXX); cp -R "$D/tasks/$T/." "$W/"
P="$(cat "$D/tasks/$T.prompt")"; printf '%s\n' "$P" > "$R/prompt.txt"
TO=1200

codex_run() {
  ( cd "$W" && timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json \
      -o "$R/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
}

# Kimi's output goes to Moonshot: its shell runs under sandbox/agent.sb with an empty scratch HOME.
kimi_run() {
  local REAL="$HOME" SH; SH=$(mktemp -d /tmp/khome-XXXXXX)
  ( cd "$W" && export HOME="$SH" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      env KIMI_CODE_HOME="$REAL/.kimi-code" timeout $TO "$REAL/.kimi-code/bin/kimi" -p "$P" --output-format stream-json \
      < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?; rm -rf "$SH"; return $rc
}

# The codex lane's run under sandbox/agent.sb. Codex gets an empty scratch HOME and CODEX_HOME, so the real ~/.codex
# (auth.json, MCP servers) is not visible; it logs in with CODEX_API_KEY from the environment instead.
# -o writes into a scratch folder in /tmp (allowed by the profile) and is copied out after sandbox-exec returns:
# inside the sandbox a denied write doesn't stop codex, it only drops the answer while the exit code stays 0.
codex_sandboxed_run() {
  [ -n "${CODEX_API_KEY:-}" ] || { echo "codex-sandboxed: CODEX_API_KEY is not set" >&2; return 2; }
  local REAL="$HOME" SH S rc; SH=$(mktemp -d /tmp/chome-XXXXXX); mkdir "$SH/.codex"; S=$(mktemp -d /tmp/cout-XXXXXX)
  ( cd "$W" && export HOME="$SH" CODEX_HOME="$SH/.codex" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json \
      -o "$S/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  rc=$?
  cp "$S/final.txt" "$R/final.txt" 2>/dev/null
  rm -rf "$SH" "$S"
  # Don't trust the exit code alone: a run that exits 0 without its answer file failed.
  if [ $rc -eq 0 ] && [ ! -s "$R/final.txt" ]; then
    echo "codex-sandboxed: exit 0 but no final.txt, see $R/agent.err" >&2; rc=1
  fi
  return $rc
}

start=$(date +%s)
case $A in
  codex) codex_run;;
  codex-sandboxed) codex_sandboxed_run;;
  kimi)  kimi_run;;
  *) echo "unknown lane $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
echo "{\"task\":\"$T\",\"lane\":\"$A\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
python3 "$D/check_answer.py" "$R" > "$R/answer.json"
rm -rf "$W"
echo "$T-$A-r$REP rc=$rc answer=$(python3 -c "import json;print(len(json.load(open('$R/answer.json'))['final']))" 2>/dev/null) chars"
