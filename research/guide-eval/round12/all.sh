#!/usr/bin/env bash
# Eight lanes in parallel: four agents x two tasks, 50 runs each (400 in total). Repetition 0 = smoke runs, not counted.
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"; date > all.started
for a in claude-haiku codex-sol-low kimi-k31 claude-deepseek; do for s in h p; do "$D/lane.sh" "$a" "$s" & done; done
wait
date > all.finished
