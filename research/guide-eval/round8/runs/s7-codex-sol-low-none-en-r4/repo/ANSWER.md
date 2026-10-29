# Intervals.icu connection failures

1. The Connect control was a document link. Browser navigation did not include the bearer token stored in `localStorage`, so `/api/intervals/auth/init` returned 401 for every athlete. The button now calls that endpoint through the authenticated API wrapper, receives the authorization URL as JSON, and then navigates to it.
2. The authorization request included both `READ` and `WRITE` for ACTIVITY and CALENDAR. Intervals.icu says `WRITE` already includes read access. The request now uses one level per resource (`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`), including the calendar write permission needed for planned workouts.
3. Intervals.icu's token response contains neither `expires_in` nor `refresh_token`: its access tokens do not expire on a one-hour timer. The old code invented a 3600-second expiry and then disconnected the athlete because no refresh token existed. The app now retains the token and marks the connection for reconnection only if an API call returns 401, which can happen after revocation.

The OAuth client ID, secret, and redirect URI in `config.py` are local placeholders. The registered production values still need to match the production environment.
