# Intervals.icu connection: causes and fixes

## Causes
1. **Connect button 401s for everyone.** It was a plain `<a href>` to `GET /api/intervals/auth/init`. A full-page navigation doesn't send the `Authorization: Bearer` header the SPA keeps in localStorage, so the server answered 401. Fix: init is now an authenticated `POST` (via the fetch wrapper) returning `{authorize_url}`, and the SPA does `window.location.assign(...)`.
2. **Authorize URL rejected (`invalid_request`) since the calendar sync shipped.** The scope string listed `ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE`. `:WRITE` implies `:READ`, and naming an area twice is rejected. Fix: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. **Rivera's connection "expired" after an hour.** Intervals tokens have no `refresh_token` or `expires_in`; they last until the athlete revokes them. The code invented a 3600s TTL and a refresher thread that marked the connection expired. Fix: removed the TTL and refresher. A 401 from Intervals now clears the token and sets the status to "expired, reconnect" (lazy revocation handling).
4. **Token exchange sent extra fields** (`grant_type`, `redirect_uri`). Intervals wants only `client_id`, `client_secret` and `code`. I removed the extras. This is based on the colleague's note and I could not verify it against the live service.

Also: the signed `state` now carries a `purpose` claim (`intervals_oauth`) that is checked in the callback.

## Colleague's note: what applied
- Applied: all four quirks (no refresh/expiry, Duplicate scope, standard-lite exchange, POST init), plus a purpose claim in `state` and the lazy 401 handling.
- Not applied: a JWT for `state` (this is stdlib-only, so I kept the existing HMAC-signed state with its 15-minute TTL). I did not add encryption at rest or the account-mismatch guard on reconnect, because the store is in memory in this dev server. Both are worth adding in prod.
- Not verified: nothing was run against real Intervals.icu (no credentials or network use). `config.py` still holds placeholder client values.
