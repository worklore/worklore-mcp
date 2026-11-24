#!/usr/bin/env bash
# Prisma rerun with the target named ("upgrade Prisma to version 8"), her call 2026-11-16: four lanes, 50 runs each.
# 16 passes, 30 minutes apart: Codex and Kimi hit their 5-hour limits overnight.
D="$(cd "$(dirname "$0")" && pwd)"; cd "$D"; date > all-p8.started
for a in claude-haiku codex-sol-low kimi-k31 claude-deepseek; do LIMIT_PASSES=16 "$D/lane.sh" "$a" p8 & done
wait; date > all-p8.finished
