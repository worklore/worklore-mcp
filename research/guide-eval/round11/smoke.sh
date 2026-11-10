#!/usr/bin/env bash
# One real run per OpenRouter lane (s11, the shortest task, ticket arm), as rep 0: make_table.py skips rep 0, so smoke
# runs never enter the results. Checks: the key works, the log is parsed (final answer, commands), cost per run,
# and that no key value survived in the run folder. Costs a few cents.
D="$(cd "$(dirname "$0")" && pwd)"
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  OPENROUTER_API_KEY="$(aws ssm get-parameter --name /worklore/openrouter-api-key --with-decryption --query Parameter.Value --output text 2>/dev/null)"
fi
[ -n "$OPENROUTER_API_KEY" ] || { echo "no OpenRouter key in SSM /worklore/openrouter-api-key"; exit 1; }
export OPENROUTER_API_KEY
AGENTS=("$@"); [ ${#AGENTS[@]} -eq 0 ] && AGENTS=(codex-oss vibe-devstral)
for a in "${AGENTS[@]}"; do
  "$D/run.sh" s11 "$a" ticket 0
  R="$D/runs/s11-$a-ticket-r0"
  python3 - "$R" <<'PY'
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[1]), "..", "graders"))
from common import commands, final_response, answer
R = sys.argv[1]; m = json.load(open(os.path.join(R, "meta.json"))); g = json.load(open(os.path.join(R, "grade.json")))
print(f"  meta: exit {m['exit_code']}, {m['wall_s']} s, limit {m['limit']}, key_hits {m['key_hits']}, PASS {g.get('PASS')}")
print(f"  commands parsed: {len(commands(R))}; final answer: {len(final_response(R))} chars; ANSWER.md: {len(answer(R))} chars")
e = os.path.join(R, "vibe", "export.json")
if os.path.exists(e):
    x = json.load(open(e)); print(f"  vibe export: outcome {x.get('outcome')}, cost ${x.get('cost_usd')}, usage {x.get('usage')}")
for line in open(os.path.join(R, "agent.log"), errors="ignore"):
    if '"turn.completed"' in line: print("  codex usage:", json.loads(line).get("usage"))
PY
  grep -rlF -- "$OPENROUTER_API_KEY" "$R" >/dev/null 2>&1 && echo "  !! key value still present in $R" || echo "  key value not present in the run folder"
done
