# Causes

1. **The Connect button did not send the athlete's sign-in token.** It was a normal link, so the browser navigated directly to `/api/intervals/auth/init` instead of using the SPA's fetch wrapper, which adds `Authorization: Bearer ...`. The server therefore returned 401, as captured in `logs/connect-attempt.log`. The button now uses the authenticated API wrapper to obtain the authorize URL, then navigates to it.

2. **The authorize request asked for conflicting access levels.** It included both `READ` and `WRITE` for `ACTIVITY` and `CALENDAR`. Intervals.icu defines `WRITE` as including `READ`, so each scope must be requested with only one access level. The redundant pairs caused the provider's `invalid_request` response. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, preserving the required access. See the [Intervals.icu OAuth documentation](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759).

3. **The one-hour expiry was invented by tricoach, not supplied by Intervals.icu.** Rivera's token response had neither `expires_in` nor `refresh_token`. The server treated a missing `expires_in` as 3,600 seconds and then marked the connection expired. A missing refresh token did not cause the expiry. The server now leaves `expires_at` unset when the provider supplies no lifetime, and the background refresher leaves that connection connected.
