#!/usr/bin/env bash
# usage: run.sh <task> <lane> [rep]
# lanes: codex           Codex CLI, unsandboxed
#        codex-sandboxed Codex CLI under sandbox/agent.sb (no reading or writing the real home), scratch HOME
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

# Codex under the same sandbox as kimi. Codex auth is an OAuth login in the real ~/.codex, which the profile hides,
# so this lane authenticates with CODEX_API_KEY from the environment and gets an empty scratch CODEX_HOME.
# -o writes into a scratch folder in /tmp: inside sandbox-exec a write under the real home is denied, and codex
# still exits 0 without the file. The file is copied into the run folder after sandbox-exec returns.
codex_sandboxed_run() {
  [ -n "${CODEX_API_KEY:-}" ] || { echo "codex-sandboxed needs CODEX_API_KEY in the environment (the real ~/.codex login is hidden)" >&2; return 2; }
  local REAL="$HOME" SH SCR; SH=$(mktemp -d /tmp/khome-XXXXXX); SCR=$(mktemp -d /tmp/cout-XXXXXX); mkdir -p "$SH/.codex"
  ( cd "$W" && export HOME="$SH" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      env CODEX_HOME="$SH/.codex" timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json \
      -o "$SCR/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?
  if [ -s "$SCR/final.txt" ]; then cp "$SCR/final.txt" "$R/final.txt"
  elif [ $rc -eq 0 ]; then echo "codex-sandboxed: codex exited 0 but wrote no final message (see agent.err)" >&2; rc=3; fi
  rm -rf "$SH" "$SCR"; return $rc
}

# Kimi's output goes to Moonshot: its shell runs under sandbox/agent.sb with an empty scratch HOME.
kimi_run() {
  local REAL="$HOME" SH; SH=$(mktemp -d /tmp/khome-XXXXXX)
  ( cd "$W" && export HOME="$SH" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      env KIMI_CODE_HOME="$REAL/.kimi-code" timeout $TO "$REAL/.kimi-code/bin/kimi" -p "$P" --output-format stream-json \
      < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?; rm -rf "$SH"; return $rc
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
