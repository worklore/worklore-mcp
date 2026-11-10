#!/usr/bin/env bash
# usage: run.sh <task> <lane> [rep]
# lanes: codex            Codex CLI, unsandboxed
#        codex-sandboxed  Codex CLI under sandbox/agent.sb (no reading or writing the real home), scratch HOME
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

# Kimi's output goes to Moonshot: its shell runs under sandbox/agent.sb with an empty scratch HOME.
kimi_run() {
  local REAL="$HOME" SH; SH=$(mktemp -d /tmp/khome-XXXXXX)
  ( cd "$W" && export HOME="$SH" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      env KIMI_CODE_HOME="$REAL/.kimi-code" timeout $TO "$REAL/.kimi-code/bin/kimi" -p "$P" --output-format stream-json \
      < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?; rm -rf "$SH"; return $rc
}

# Same Codex run under sandbox/agent.sb, with a scratch HOME and CODEX_HOME. Codex writes its last message to -o, and
# the profile denies writes to the real home, so -o points into the scratch folder in /tmp and the file is copied to
# the run folder after sandbox-exec returns (a denied -o write does not stop Codex: it only logs and exits 0).
# The profile also denies reads of the real home, so Codex's login and config are copied in before the sandbox starts.
codex_sandboxed_run() {
  local REAL="$HOME" S; S=$(mktemp -d /tmp/hcodex-XXXXXX); mkdir -p "$S/home" "$S/codex"
  for f in auth.json config.toml; do [ -f "$REAL/.codex/$f" ] && cp "$REAL/.codex/$f" "$S/codex/$f"; done
  ( cd "$W" && export HOME="$S/home" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      env CODEX_HOME="$S/codex" timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
      -C "$W" --json -o "$S/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?
  if [ -f "$S/final.txt" ]; then cp "$S/final.txt" "$R/final.txt"; else echo "codex-sandboxed: no final.txt was written" >&2; fi
  grep -q "Operation not permitted" "$R/agent.err" && echo "codex-sandboxed: a write was denied by the sandbox, see agent.err" >&2
  rm -rf "$S"; return $rc
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
