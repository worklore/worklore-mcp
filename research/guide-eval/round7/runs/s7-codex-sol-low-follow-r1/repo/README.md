# tricoach

Backend + single-page app for a small triathlon coaching practice. Coaches
plan the week; athletes see it and connect their Intervals.icu account so the
app can read wellness data and push planned workouts to their calendar. The
athlete signs in to tricoach (token in `localStorage`, sent as
`Authorization: Bearer` by the SPA's fetch wrapper), then clicks
"Connect Intervals.icu", which runs the OAuth flow against Intervals.

`server.py` requires `cryptography` (`python3 -m pip install cryptography`; then `python3 server.py`, port 8766) and keeps
everything in memory; the shape is the same as the Postgres tables in prod.
Dev sign-in tokens: `tok-okafor` (default in the SPA) and `tok-rivera`.
`config.py` holds the OAuth client placeholders. `logs/` has what we captured
while looking into the connection problems.
