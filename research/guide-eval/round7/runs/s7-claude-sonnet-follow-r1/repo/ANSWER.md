# Causes

1. **Connect always 401'd: init was a GET link.** The button was `<a href="/api/intervals/auth/init">`;
   a full-page navigation doesn't send the `Authorization` header (kept in localStorage, sent only by
   the fetch wrapper), so every athlete got `{"error":"unauthorized"}`.
   Fix: init is now an authenticated `POST` returning `{authorize_url}`; the SPA calls it via `api()`
   and does `window.location.assign(authorize_url)`.
2. **Authorize URL rejected with `invalid_request`: duplicate scope.** Since the calendar sync
   (2026-10-02) the scope was `ACTIVITY:READ,ACTIVITY:WRITE,...,CALENDAR:READ,CALENDAR:WRITE`.
   `:WRITE` implies `:READ`, and naming an area twice is invalid. Fix: each area once
   (`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`).
3. **"Expired after an hour": invented token TTL.** Intervals tokens have no `refresh_token` or
   `expires_in` and live until revoked. The code defaulted to a 3600s TTL and a background job
   expired the connection (Rivera, 2026-09-19). Fix: removed TTL, `expires_at` and the refresher;
   revocation is handled lazily - a 401 from the API clears the token and marks the user "reconnect".
4. **Token exchange sent extra fields.** It sent `grant_type` and `redirect_uri`; Intervals wants only
   `client_id`, `client_secret`, `code`. Fixed.

Also: `state` is now a signed HS256 JWT (`sub`, `purpose=intervals_oauth`, 15-min `exp`) checked
before the code exchange, and a reconnect with a different athlete id than the stored one is
rejected (409).

Not done / caveats: not tested against the real Intervals.icu (needs real client credentials).
The token is held in the in-memory store; encrypt it at rest in the real database (stdlib has no
cipher, so I left a note in `store_connection`). `config.APP_SECRET`/client secret are still dev placeholders.
