#!/usr/bin/env bash
D=/private/tmp/claude-501/-Users-valentinakoniukhova-projects-worklore/45aea092-d156-403e-85fa-11e392426b83/scratchpad/guide-eval-r5
for R in "$D"/runs/*/; do [ -f "$R/meta.json" ] || continue; S=$(basename "$R" | cut -d- -f1); python3 "$D/graders/grade_$S.py" "$R" > "$R/grade.json" 2> "$R/grade.err"; done
