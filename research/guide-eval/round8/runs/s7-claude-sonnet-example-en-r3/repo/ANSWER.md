# Causes and fixes

1. **Connect button 401s for everyone.** It was a plain `<a href>` to `GET /api/intervals/auth/init`. A page navigation doesn't send the `Authorization: Bearer` header the SPA keeps in localStorage, so the server returned `{"error":"unauthorized"}`. Fix: init is now an authenticated `POST` returning `{authorize_url}`. The button uses `api()` (fetch with the header) and then calls `window.location.assign(...)` (`server.py`, `static/app.js`).
2. **Authorize URL rejected with 400 `invalid_request` (since the 2026-10-02 calendar sync).** The scope was `ACTIVITY:READ,ACTIVITY:WRITE,...,CALENDAR:READ,CALENDAR:WRITE`. Intervals rejects naming an area twice because `:WRITE` implies `:READ` ("Duplicate scope"). Fix: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (`config.py`). This is inferred from the logs and the note. I couldn't test it against the real Intervals.
3. **Connection "expired" after an hour.** Intervals tokens have no `refresh_token` or `expires_in` and last until revoked. The code invented a 3600s TTL (`DEFAULT_TOKEN_TTL`), and the refresher then marked the token expired and wiped it. Fix: no expiry when the provider gives none (`expires_at=None`, and the refresher skips those). Revocation is now handled lazily: a 401 from Intervals marks the connection "expired, reconnect".
4. **Token exchange sent extra fields** (`grant_type`, `redirect_uri`). It now sends only `client_id`, `client_secret` and `code`, per the note. I couldn't verify this against the real service.

## Colleague's note: what applied
- Applied: points 1 (no refresh/expiry, lazy 401 handling), 2 (Duplicate scope), 3 (minimal exchange; the `athlete` object in the response was already used), 4 (POST init). I also added the account-mismatch guard on reconnect.
- Not applied: switching `state` to a JWT with a `purpose` claim (the existing HMAC-signed state with a 15-minute TTL already does the job), and encryption at rest (the store here is in memory; do it when moving to Postgres).

Not tested against a live Intervals.icu account. I only syntax-checked the code.
