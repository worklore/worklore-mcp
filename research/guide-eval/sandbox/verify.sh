#!/usr/bin/env bash
# sandbox/verify.sh: run INSIDE the sandbox, the same way the agent is launched:
#
#   . sandbox/env.sh; sandbox_exec bash sandbox/verify.sh [cli]
#
# Prints the NAMES of the variables this process received, never a value, and exits
#   0  every name is in the allowlist and no value has a secret shape
#   1  a name is outside the allowlist
#   2  a value matches a secret shape (the name is printed, the value is not)
#   3  both
# Run it without the sandbox (`bash sandbox/verify.sh`) to see what the agent used to get.
set -u
D="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=env.sh
. "$D/env.sh"
SANDBOX_CLI="${1:-${SANDBOX_CLI:-}}"

# Secret shapes. Checked with bash [[ =~ ]] so the value never leaves this process.
shapes=(
  'AKIA[0-9A-Z]{16}'                     # AWS access key id
  '(^|[^A-Za-z0-9])ghp_[A-Za-z0-9]{10,}'  # GitHub personal token
  '(^|[^A-Za-z0-9])sk-[A-Za-z0-9_-]{10,}' # OpenAI / Anthropic style key
  'sk_live_'                             # Stripe live key
  'xox[bp]-'                             # Slack token
  '[0-9a-fA-F]{32,}'                     # 32+ hex (md5, uuid without dashes, many API keys)
)
shape_names=(aws-akia github-ghp sk-key stripe-live slack-xox hex32)
# 40+ base64-ish. For path-like variables a run must not cross a "/", or every long
# directory path matches; for every other variable "/" counts, as in real base64.
b64_full='[A-Za-z0-9+/=_-]{40,}'
b64_noslash='[A-Za-z0-9+=_-]{40,}'
pathlike=' PATH HOME TMPDIR PWD OLDPWD _ SHELL '

allowed=" $(sandbox_names | tr '\n' ' ') "
bad_name=0; bad_value=0; count=0
# compgen -e lists exported names; `env | cut -d= -f1` breaks on multi-line values.
for n in $(compgen -e | sort); do
  count=$((count+1))
  v="${!n}"
  flag=""
  case "$allowed" in *" $n "*) ;; *) flag="EXTRA"; bad_name=1;; esac
  hit=""
  for i in "${!shapes[@]}"; do
    [[ "$v" =~ ${shapes[$i]} ]] && hit="${hit:+$hit,}${shape_names[$i]}"
  done
  # A value that is a path (starts with "/") or a path list gets the no-slash class too,
  # otherwise JAVA_HOME and friends trip the shape on a long directory name.
  if [[ "$pathlike" == *" $n "* || "$v" == /* ]]; then
    [[ "$v" =~ $b64_noslash ]] && hit="${hit:+$hit,}base64-40"
  else
    [[ "$v" =~ $b64_full ]] && hit="${hit:+$hit,}base64-40"
  fi
  if [ -n "$hit" ]; then flag="${flag:+$flag }SECRET-SHAPE($hit)"; bad_value=1; fi
  printf '  %-6s %s\n' "${flag:-ok}" "$n"
done
rc=$((bad_name + 2*bad_value))
echo "verify: $count names in the child, cli=${SANDBOX_CLI:-none}, result=$([ $rc = 0 ] && echo PASS || echo FAIL) (exit $rc)"
exit $rc
