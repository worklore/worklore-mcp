#!/usr/bin/env bash
# usage: run.sh <task> <lane> [rep]
# lanes: codex            Codex CLI, unsandboxed
#        codex-sandboxed  Codex CLI under sandbox/agent.sb, scratch HOME
#        kimi             Kimi Code under sandbox/agent.sb (no reading or writing the real home), scratch HOME
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

codex_sandboxed_run() {
  local REAL="$HOME" SH SC; SH=$(mktemp -d /tmp/chome-XXXXXX); SC=$(mktemp -d /tmp/cscratch-XXXXXX)
  ( cd "$W" && export HOME="$SH" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json \
      -o "$SC/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?
  [ -f "$SC/final.txt" ] && cp "$SC/final.txt" "$R/final.txt"
  rm -rf "$SH" "$SC"; return $rc
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
  codex)           codex_run;;
  codex-sandboxed) codex_sandboxed_run;;
  kimi)            kimi_run;;
  *) echo "unknown lane $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
echo "{\"task\":\"$T\",\"lane\":\"$A\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
python3 "$D/check_answer.py" "$R" > "$R/answer.json"
rm -rf "$W"
echo "$T-$A-r$REP rc=$rc answer=$(python3 -c "import json;print(len(json.load(open('$R/answer.json'))['final']))" 2>/dev/null) chars"
