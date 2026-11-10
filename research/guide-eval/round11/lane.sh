#!/usr/bin/env bash
# usage: lane.sh <agent> [reps]  — as round 8: reps in the OUTER loop, so a lane stopped early still holds complete
# repetitions for every cell; story order rotates per agent; a run marked "limit" is deleted and redone on a later
# pass, passes repeat 30 minutes apart until every cell has a result or LIMIT_PASSES is reached.
# The OpenRouter lanes (codex-oss, vibe-devstral) read the key from SSM /worklore/openrouter-api-key into the
# environment (never printed), and stop at once when a run writes STOP-<agent> (key rejected or credits gone).
D="$(cd "$(dirname "$0")" && pwd)"
A=$1; REPS=${2:-5}
# Stories since the 2026-11-09 amendment (plan.md): the three new ones the screen kept and the two controls.
ALL=(n4 n6 n10 s8 s11)
ARMS=(none story ticket)
case $A in
  kimi-k31) ARMS=(ticket);;                      # optional lane
  claude-opus) ALL=(n4 n6 n10); ARMS=(none);;    # reference for question A: frontier without a story
  agy-oss) ALL=(n4 n6 n10); ARMS=(none story);;  # reference for question B: GPT-OSS in Antigravity
esac
case $A in claude-haiku) k=4;; codex-sol-low) k=3;; codex-oss) k=1;; vibe-devstral) k=2;; claude-opus) k=1;; agy-oss) k=2;; *) k=0;; esac
ORDER=("${ALL[@]:$k}" "${ALL[@]:0:$k}")
LIMIT_PASSES=${LIMIT_PASSES:-10}
case $A in codex-oss|vibe-devstral)
  if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    OPENROUTER_API_KEY="$(aws ssm get-parameter --name /worklore/openrouter-api-key --with-decryption --query Parameter.Value --output text 2>/dev/null)"
  fi
  [ -n "$OPENROUTER_API_KEY" ] || { echo "no OpenRouter key: put it in SSM /worklore/openrouter-api-key (SecureString)" | tee -a "$D/lane-$A.out"; exit 1; }
  export OPENROUTER_API_KEY;;
esac
stopped() { [ -f "$D/STOP-$A" ] && { echo "LANE_STOPPED: $(tail -1 "$D/STOP-$A")" >> "$D/lane-$A.out"; exit 1; }; }
bad() { [ -f "$1/meta.json" ] && grep -qE '"limit":true' "$1/meta.json"; }
one() { # one <story> <arm> <rep>
  local R="$D/runs/$1-$A-$2-r$3"
  if [ -f "$R/grade.json" ]; then bad "$R" || return; echo "REDO $1 $2 r$3" >> "$D/lane-$A.out"; rm -rf "$R"; fi
  stopped
  "$D/run.sh" "$1" "$A" "$2" "$3" >> "$D/lane-$A.out" 2>&1
  if bad "$R"; then echo "LIMIT $1 $2 r$3 (will redo)" >> "$D/lane-$A.out"; rm -rf "$R"; fi
  stopped
}
missing() { local n=0; for REP in $(seq 1 "$REPS"); do for S in "${ALL[@]}"; do for ARM in "${ARMS[@]}"; do
  [ -f "$D/runs/$S-$A-$ARM-r$REP/grade.json" ] || n=$((n+1)); done; done; done; echo $n; }
pass=0
while :; do
  for REP in $(seq 1 "$REPS"); do for S in "${ORDER[@]}"; do for ARM in "${ARMS[@]}"; do one "$S" "$ARM" "$REP"; done; done; done
  pass=$((pass+1)); m=$(missing)
  [ "$m" = 0 ] && break
  [ "$pass" -ge "$LIMIT_PASSES" ] && { echo "LANE_GAVE_UP after $pass passes, $m cells missing" >> "$D/lane-$A.out"; break; }
  echo "pass $pass done, $m cells missing; sleeping 30 min" >> "$D/lane-$A.out"; sleep 1800
done
echo LANE_DONE >> "$D/lane-$A.out"
