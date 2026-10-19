#!/usr/bin/env bash
# Runs every lane. Claude ×3 and Codex ×2 in parallel; Antigravity lanes two at a time.
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r5
cd "$D"; date > all.started
"$D/lane.sh" claude-opus & "$D/lane.sh" claude-sonnet & "$D/lane.sh" claude-haiku &
"$D/lane.sh" codex-sol & "$D/lane.sh" codex-sol-low &
( "$D/lane.sh" agy-argon-high; "$D/lane.sh" agy-argon-low ) &
( "$D/lane.sh" agy-flash-low; "$D/lane.sh" agy-oss ) &
wait
date > all.finished
