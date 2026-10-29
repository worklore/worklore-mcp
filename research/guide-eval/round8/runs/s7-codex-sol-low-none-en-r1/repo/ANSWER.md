# Intervals.icu connection failures

1. **Connect returned 401.** The SPA used a normal link to `/api/intervals/auth/init`. Browser navigation does not include the bearer token held in `localStorage`, while that endpoint requires the token. The button now calls the endpoint through the authenticated fetch wrapper, receives an authorize URL, and navigates to it.
2. **The authorize URL returned 400.** The requested scopes included both READ and WRITE for ACTIVITY and CALENDAR. Intervals.icu treats these as duplicate resource scopes; WRITE includes READ. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. **A working connection was discarded after an hour.** Intervals.icu returns an access token without a refresh token or `expires_in`; its token has no scheduled expiry. The app invented a one-hour lifetime, then marked the valid token expired because it could not refresh it. It now keeps the token until Intervals.icu rejects it with HTTP 401, when it asks the athlete to reconnect.

The development OAuth credentials remain placeholders. End-to-end consent requires the configured, approved Intervals.icu client and its registered redirect URI.
