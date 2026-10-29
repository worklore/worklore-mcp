#!/usr/bin/env bash
# Codex usage window resets at 09:42; start both Codex fill lanes just after.
D="$(cd "$(dirname "$0")" && pwd)"
while [ "$(date +%H%M)" -lt 0943 ]; do sleep 60; done
date > "$D/codex_fill.started"
"$D/lane.sh" codex-sol & "$D/lane.sh" codex-sol-low & wait
date > "$D/all.finished"
