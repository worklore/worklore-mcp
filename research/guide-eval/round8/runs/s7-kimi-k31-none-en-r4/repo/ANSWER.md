# Causes

1. **The Connect link bypassed tricoach authentication.** The SPA stores its token in `localStorage` and normally adds it with the `fetch` wrapper, but Connect was a plain link. Browser navigation therefore sent no `Authorization` header, and `/api/intervals/auth/init` returned 401 (`logs/connect-attempt.log:5`). Connect now uses the authenticated API wrapper and navigates to the returned Intervals.icu authorize URL.

2. **The calendar rollout produced an invalid scope request.** The failing authorize URL requested `CALENDAR:READ,CALENDAR:WRITE` along with separate read and write activity scopes, and Intervals.icu rejected it with `invalid_request` before consent (`logs/connect-attempt.log:19`). A `WRITE` scope already includes read access. The request now uses only `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, retaining the required activity and planned-workout access without the redundant scope entries.

3. **The app invented a one-hour expiry when the provider supplied none.** Rivera's token response had neither `expires_in` nor `refresh_token` (`logs/connect-attempt.log:35`). The app substituted a 3600-second lifetime and then revoked a still-valid local connection when that timer elapsed (`logs/connect-attempt.log:37`). Tokens now expire locally only when Intervals.icu explicitly provides `expires_in`; tokens with an explicit expiry still use the refresh flow.
