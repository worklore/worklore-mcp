# Intervals.icu connection: causes and fixes

## Causes
1. **Connect always 401'd (every athlete).** The button was a plain link to `GET /api/intervals/auth/init`. A full-page navigation doesn't send the `Authorization: Bearer` header, which the SPA only attaches via `fetch`. Fix: init is now an authenticated `POST` returning `{authorize_url}`. The SPA calls it with `fetch` and then runs `window.location.assign(...)` (`server.py`, `static/app.js`).
2. **Authorize URL returned 400 `invalid_request` (the hand-pasted link, since 2026-10-02).** The calendar-sync change added `CALENDAR:READ` and `ACTIVITY:READ` next to the `:WRITE` scopes. Intervals rejects an area named twice, because `:WRITE` implies `:READ`. The 400 body doesn't name the parameter, and I couldn't reach Intervals to confirm. This is the best fit for the symptoms. Fix: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (`config.py`).
3. **Rivera's token "expired" after an hour.** Intervals tokens have no `refresh_token` and no `expires_in`. They last until the athlete revokes them. The code invented a 3600s default TTL, and the refresher then marked the connection expired. Fix: no invented expiry (`expires_at` is `None` unless the provider sends one), and the refresher skips such tokens. Revocation is now handled lazily: a 401 from Intervals marks the connection "expired, reconnect".

## Colleague's note
- **Applied:** point 1 (no refresh/expiry, handle 401 lazily), point 2 (no duplicate scopes), point 4 (POST init plus `window.location.assign`).
- **Not applied:**
  - Dropping `grant_type` and `redirect_uri` from the token exchange. Rivera's logged exchange succeeded with them, so I left it alone.
  - JWT `state` and the account-mismatch guard. The existing HMAC-signed state with a 15-minute TTL already carries the user identity.
  - Encrypting the token at rest. The store is in-memory here, and prod storage isn't in this repo.

## Not verified
I couldn't test against the real Intervals.icu. I only syntax-checked `server.py`. I didn't run the server or the browser flow.
