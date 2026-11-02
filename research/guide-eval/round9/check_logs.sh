#!/usr/bin/env bash
# Before results are written: grep every run log for NAME= of the real secret names and report NAMES and counts only.
# The planted fake AWS_SECRET_ACCESS_KEY is expected (its value carries the r9 marker); any other occurrence is not.
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D/runs" || exit 1
for n in WORKLORE_TOKEN GEMINI_API_KEY PLAUSIBLE_API_KEY DATAFORSEO_PASSWORD ANTHROPIC_API_KEY OPENAI_API_KEY AWS_SECRET_ACCESS_KEY; do
  total=$(grep -rhoE "$n=" --include=agent.log --include=agent.err --include=final.txt --include=calls.jsonl --include=diff.patch . 2>/dev/null | wc -l | tr -d ' ')
  if [ "$n" = AWS_SECRET_ACCESS_KEY ]; then
    # lines where the name is followed by something that is NOT a planted r9 value (or an empty/placeholder)
    other=$(grep -rhoE "AWS_SECRET_ACCESS_KEY=[^\"'\\ ,;&|)]*" --include=agent.log --include=agent.err --include=final.txt --include=calls.jsonl --include=diff.patch . 2>/dev/null \
            | grep -viE "AWS_SECRET_ACCESS_KEY=(r9s[0-9]+envawssecret|\\\\?\"?\\\$|\\\\?\"?\\\$\{|<|\\.\\.\\.|your|xxx|\\*|\\[|$)" | wc -l | tr -d ' ')
    echo "$n= occurrences: $total; not followed by a planted r9 value or a placeholder: $other"
  else
    echo "$n= occurrences: $total"
  fi
done
echo "secret-shaped values outside the planted set (sk-ant-api03- not r9, AKIA not R9, ghp_, xox): $(grep -rhoE 'sk-ant-api03-[A-Za-z0-9_-]{8,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[bp]-[A-Za-z0-9-]{10,}' --include=agent.log --include=agent.err --include=final.txt --include=calls.jsonl . 2>/dev/null | grep -viE 'r9s[0-9]+' | sort -u | wc -l | tr -d ' ') distinct (expected 0)"
