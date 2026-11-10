#!/usr/bin/env bash
# usage: run.sh <task> <lane> [rep]
# lanes: codex            Codex CLI, unsandboxed
#        codex-sandboxed  Codex CLI executed inside sandbox/agent.sb (no real HOME access)
#        kimi              Kimi Code under sandbox/agent.sb (no reading or writing the real home), scratch HOME
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

# Codex run inside the macOS sandbox, mirroring the Kimi lane. The sandbox denies
# reads/writes to the real $HOME, so we give the agent a temporary HOME and a
# separate scratch directory for the final output file. After the sandbox exits,
# we copy the result back into the run folder.
codex_sandboxed_run() {
  # Preserve the real HOME for the sandbox profile.
  local REAL_HOME="$HOME"
  # Temporary HOME that the sandboxed process sees (empty to avoid leaking real files).
  local SANDBOX_HOME; SANDBOX_HOME=$(mktemp -d /tmp/codex-home-XXXXXX)
  # Scratch directory where Codex can safely write its output.
  local SCRATCH; SCRATCH=$(mktemp -d /tmp/codex-scratch-XXXXXX)

  ( cd "$W" && export HOME="$SANDBOX_HOME" \
      && sandbox-exec -D HOME="$REAL_HOME" -f "$D/sandbox/agent.sb" \
         timeout $TO codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox \
         -C "$W" --json -o "$SCRATCH/final.txt" "$P" < /dev/null \
         > "$R/agent.log" 2> "$R/agent.err" )
  local rc=$?
  # Bring the generated final.txt back into the run folder if it exists.
  if [ -f "$SCRATCH/final.txt" ]; then
    cp "$SCRATCH/final.txt" "$R/final.txt"
  fi
  rm -rf "$SANDBOX_HOME" "$SCRATCH"
  return $rc
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
