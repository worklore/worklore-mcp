#!/usr/bin/env bash
# The three lanes in parallel. Records t0 (ms since the epoch) for the CloudWatch read-back.
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"; date > all.started; date +%s000 > t0_ms
"$D/lane.sh" claude-opus & "$D/lane.sh" codex-sol & "$D/lane.sh" agy-flash-low &
wait
date > all.finished
