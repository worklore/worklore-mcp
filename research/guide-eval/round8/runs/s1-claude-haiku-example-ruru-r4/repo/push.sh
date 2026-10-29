#!/usr/bin/env bash
# usage: ./push.sh event.json   (needs INTERVALS_API_KEY and ATHLETE_ID)
set -eu
curl -sS -u "API_KEY:${INTERVALS_API_KEY}" -H 'Content-Type: application/json' \
  -X POST "https://intervals.icu/api/v1/athlete/${ATHLETE_ID}/events" \
  --data-binary @"$1"
