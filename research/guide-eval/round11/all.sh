#!/usr/bin/env bash
# The four main lanes, 75 runs each (5 stories × 3 arms × 5 reps), and the two reference lanes on the new stories
# (claude-opus none, 15 runs; agy-oss none and story, 30 runs), all in parallel. Run smoke.sh first and read its output.
# kimi-k31 (ticket arm only, 30 runs) is optional: start it by hand with ./lane.sh kimi-k31
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"; date > all.started
for a in claude-haiku codex-sol-low codex-oss vibe-devstral claude-opus agy-oss; do "$D/lane.sh" "$a" & done
wait
date > all.finished
