#!/usr/bin/env bash
# Every lane except the two Gemini 4 Argon ones (Google AI Pro quota exhausted until ~2026-10-25).
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r7
cd "$D"; date > all.started
"$D/lane.sh" claude-opus & "$D/lane.sh" claude-sonnet & "$D/lane.sh" claude-haiku &
"$D/lane.sh" codex-sol & "$D/lane.sh" codex-sol-low &
"$D/lane.sh" agy-flash-low & "$D/lane.sh" agy-oss &
wait
date > all.finished
