# tricoach

Backend + single-page app for a small triathlon coaching practice. Coaches
plan the week; athletes see it and connect their Intervals.icu account so the
app can read wellness data and push planned workouts to their calendar. The
athlete signs in to tricoach (token in `localStorage`, sent as
`Authorization: Bearer` by the SPA's fetch wrapper), then clicks
"Connect Intervals.icu", which runs the OAuth flow against Intervals.

Install `cryptography` (`pip install -r requirements.txt`), then run
`python3 server.py` on port 8766. This demo keeps encrypted connection
records in memory; the shape is the same as the Postgres tables in prod.
Dev sign-in tokens: `tok-okafor` (default in the SPA) and `tok-rivera`.
Set `APP_SECRET`, `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET`, and
`INTERVALS_REDIRECT_URI` in the environment for a real OAuth client. Keep
`APP_SECRET` stable so stored tokens can be decrypted. `config.py` has local
placeholders. `logs/` has what we captured while looking into the connection
problems.
