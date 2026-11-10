#!/usr/bin/env bash
# usage: run.sh <task> <lane> [rep]
# lanes: codex            Codex CLI, unsandboxed
#        codex-sandboxed  the same Codex run under sandbox/agent.sb (no reading or writing the real home)
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

# codex-sandboxed: codex_run under sandbox/agent.sb, like kimi. Codex gets a scratch HOME and CODEX_HOME holding copies of
# config.toml and auth.json. -o goes to a scratch folder in /tmp, not the run folder: inside the sandbox a write under the
# real home is denied, and codex exits 0 anyway, so the copy-out happens after sandbox-exec returns.
codexsb_run() {
  local REAL="$HOME" SH CS CH rc
  SH=$(mktemp -d /tmp/chome-XXXXXX); CS=$(mktemp -d /tmp/cout-XXXXXX); CH="$SH/.codex"; mkdir -p "$CH"
  cp "$REAL/.codex/config.toml" "$REAL/.codex/auth.json" "$CH/"
  ( cd "$W" && export HOME="$SH" && sandbox-exec -D HOME="$REAL" -f "$D/sandbox/agent.sb" \
      env CODEX_HOME="$CH" timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -C "$W" --json \
      -o "$CS/final.txt" "$P" < /dev/null > "$R/agent.log" 2> "$R/agent.err" )
  rc=$?
  if [ -f "$CS/final.txt" ]; then cp "$CS/final.txt" "$R/final.txt"; fi
  rm -rf "$SH" "$CS"
  if [ ! -s "$R/final.txt" ]; then echo "warning: no final.txt in $R (see agent.err)" >&2; fi
  if grep -q "Operation not permitted" "$R/agent.err"; then echo "warning: a write was denied, see $R/agent.err" >&2; fi
  return $rc
}

start=$(date +%s)
case $A in
  codex) codex_run;;
  codex-sandboxed) codexsb_run;;
  kimi)  kimi_run;;
  *) echo "unknown lane $A"; exit 2;;
esac
rc=$?
end=$(date +%s)
echo "{\"task\":\"$T\",\"lane\":\"$A\",\"rep\":$REP,\"exit_code\":$rc,\"wall_s\":$((end-start))}" > "$R/meta.json"
python3 "$D/check_answer.py" "$R" > "$R/answer.json"
rm -rf "$W"
echo "$T-$A-r$REP rc=$rc answer=$(python3 -c "import json;print(len(json.load(open('$R/answer.json'))['final']))" 2>/dev/null) chars"
