# What the watch showed for event 184233 (Tempo run 45)

Intervals: LTHR 172. Watch (Forerunner 965): auto-detected LTHR 168, zones
Z1 <118, Z2 118–137, Z3 137–151, Z4 151–162, Z5 >162.

`GET /api/v1/athlete/{id}/events/184233` returned the event exactly as we sent
it (see `event-184233-as-sent.json`); `workout_doc.steps` is populated, so the
API accepted it.

| step | planned (% LTHR) | expected on watch (× 172) | watch displayed |
|---|---|---|---|
| Warm-up easy | 68–75 | 117–129 | 118–137 |
| Tempo | 88–93 | 151–160 | 151–162 |
| Float | 75–82 | 129–141 | 137–151 |
| Cool-down | 65–72 | 112–124 | 118–137 |

Every corridor shows up as one of the watch's own zone bands, not the range we
planned. Changing the watch's LTHR to 172 moves the bands but they are still
zone edges, never 151–160 or 129–141. Earlier tries: `units: "bpm"` with
absolute values made the watch show 214–249 bpm; `start_bpm`/`end_bpm` made
every target a constant 101.
