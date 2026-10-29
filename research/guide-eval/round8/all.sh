#!/usr/bin/env bash
# Every lane except the two Gemini 4 Argon ones (Google AI Pro quota, assumed exhausted).
D="$(cd "$(dirname "$0")" && pwd)"
cd "$D"; date > all.started
"$D/lane.sh" claude-opus & "$D/lane.sh" claude-sonnet & "$D/lane.sh" claude-haiku &
"$D/lane.sh" codex-sol & "$D/lane.sh" codex-sol-low &
"$D/lane.sh" agy-flash-low & "$D/lane.sh" agy-oss &
wait
date > all.finished
