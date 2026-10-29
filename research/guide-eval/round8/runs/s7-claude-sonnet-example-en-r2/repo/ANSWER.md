# Intervals.icu connect: causes and fixes

## Causes
1. **Connect button always 401s.** The button was a plain `<a href>` to `GET /api/intervals/auth/init`. A page navigation doesn't send the `Authorization` header the SPA keeps in localStorage, so the server saw no user (see `logs/connect-attempt.log`, ticket #214).
   Fix: init is now an authenticated `POST` that returns `{authorize_url}`. The button uses `fetch` and then `window.location.assign(authorize_url)`.
2. **Authorize URL returns 400 `invalid_request`** (since the calendar sync shipped on 2026-10-02). The scope string named the same area twice (`ACTIVITY:READ,ACTIVITY:WRITE`, `CALENDAR:READ,CALENDAR:WRITE`). `:WRITE` already implies `:READ`, so Intervals rejects the duplicate.
   Fix: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
   I couldn't confirm this against the live service. The log shows only a generic 400, so this follows from the colleague's note plus the scope list. Please verify against Intervals.
3. **Rivera "expired after an hour".** Intervals tokens have no `refresh_token` and no `expires_in`. They last until the athlete revokes them. The code invented a 3600s default TTL, and a background job then marked the connection expired.
   Fix: I removed the TTL, the refresher thread and `REFRESH_INTERVAL`. Revocation is now handled lazily: a 401 from the Intervals API clears the token and sets the status to "expired, reconnect".
4. **Token exchange sent extra fields.** It sent `grant_type` and `redirect_uri`. Per the note, the endpoint wants only `client_id`, `client_secret` and `code`, so I trimmed the request. This is a hardening change. Nothing in the logs shows it failed, because Rivera's exchange succeeded.

## Colleague's note: what applied
- Applied: no refresh_token and no expiry, the lazy 401 handling, the "Duplicate scope" rule, the minimal token exchange, and the POST init that returns JSON.
- Applied: the account-mismatch guard on reconnect. The callback is rejected if the athlete id differs from the stored one.
- Not applied: the signed JWT `state` with a `purpose` claim. The existing HMAC-signed state with a 15-minute TTL already carries the identity. I left it as is.
- Not applied: encrypting the token at rest. The store is in-memory here, so it only matters for the production tables.
- Not applied: the Intervals-side verification steps (real account, revoke test, duplicate-scope probe). I couldn't run them, and I don't send anything to external services.

Verification: `server.py` compiles. I did not run the flow end to end.
