#!/bin/zsh
# Nightly review of yesterday's commits, summary to Telegram.
# NB: never assign to `status` here — in zsh it is a read-only alias of $?.
set -u

REPO="$HOME/projects/shop"
OUT="$HOME/Library/Logs/nightly-review-$(date +%F).md"
ERR="$HOME/Library/Logs/nightly-review-$(date +%F).err"
NOTIFY="$HOME/bin/notify.sh"
START=$SECONDS

log() { print -r -- "$(date '+%F %T') nightly-review: $*" >&2; }

fail() {
  log "FAILED: $1"
  "$NOTIFY" "nightly review FAILED: $1" || log "notify.sh also failed (rc=$?)"
  exit 1
}

log "start (USER=${USER-unset} HOME=$HOME)"

SINCE=$(date -v-1d +%F)
PROMPT="Review the commits in this repository since $SINCE.
For each commit: one line on what it changes and whether anything looks risky
(migrations, auth, payments, deleted tests).
End with a three-line summary I can read on my phone.
Do not modify any file."

cd "$REPO" || fail "repo $REPO missing"
command -v claude >/dev/null || fail "claude not found in PATH=$PATH"

# Prompt goes through stdin, not as a multi-line argument.
print -r -- "$PROMPT" | claude -p --output-format text > "$OUT" 2> "$ERR"
rc=$?
dur=$(( SECONDS - START ))
log "claude exit=$rc after ${dur}s"
cat "$ERR" >&2

if (( rc != 0 )); then
  fail "claude exit $rc after ${dur}s: $(tail -n 3 "$ERR")"
fi
if [[ ! -s "$OUT" ]]; then
  fail "claude exit 0 but empty output after ${dur}s: $(tail -n 3 "$ERR")"
fi

summary=$(<"$OUT")
"$NOTIFY" "nightly review done (${dur}s): ${summary[1,300]}" \
  || { log "notify.sh failed (rc=$?)"; exit 1; }
log "done"
