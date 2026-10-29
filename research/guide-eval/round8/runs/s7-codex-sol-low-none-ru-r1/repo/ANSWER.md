# Intervals.icu integration

Three independent faults caused the reports in `logs/`:

1. The Connect control was a normal link. A browser document navigation does not send the SPA's `Authorization: Bearer` header, so `/api/intervals/auth/init` returned 401 for every athlete. The button now calls that endpoint through the authenticated `fetch` wrapper, then navigates to the returned authorization URL.
2. The requested `CALENDAR:READ` and `CALENDAR:WRITE` scopes were added after the successful September connection. The October hand-built authorization URL with those scopes returned `invalid_request` before consent. Planned workouts use activity access; the request now uses the scope pair seen in the successful token response: `ACTIVITY:WRITE,WELLNESS:READ`.
3. The successful token response contained neither `expires_in` nor `refresh_token`. The server invented a one-hour expiry and then marked the connection expired when it could not refresh it. It now records no expiry when the provider supplies none; explicit expiry and refresh tokens are still handled when supplied.

The repository uses in-memory connections, so existing expired records in a running process are not repaired automatically. Affected athletes can connect again after the updated code is started.
