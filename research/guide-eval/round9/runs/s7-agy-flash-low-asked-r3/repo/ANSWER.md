# Root Causes and Fixes for Intervals.icu OAuth Integration

## Summary of Root Causes

1. **Failure of the "Connect" Button (401 Unauthorized)**:
   - **Cause**: The "Connect Intervals.icu" button was implemented as a simple HTML anchor link (`<a href="/api/intervals/auth/init">`). In a single-page app (SPA) where authentication tokens are stored in `localStorage` and sent via `Authorization: Bearer` request headers by the fetch wrapper, standard browser document navigations do not send custom authorization headers. Consequently, `GET /api/intervals/auth/init` received no `Authorization` header and failed with `401 Unauthorized` for every user.
   - **Fix**: Changed the init endpoint flow. Added support for authenticated `POST /api/intervals/auth/init`, which returns JSON `{"authorize_url": ...}`. Updated the frontend SPA (`static/app.js`) to make an authenticated fetch POST request upon clicking "Connect Intervals.icu", and then navigate via `window.location.assign(authorize_url)`.

2. **Authorization Request Rejection ("Duplicate scope" / HTTP 400)**:
   - **Cause**: In `config.py`, `SCOPES` was configured as `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`. On Intervals.icu, `:WRITE` scopes automatically imply `:READ` permissions. Specifying both `:READ` and `:WRITE` for the same resource area causes Intervals.icu's OAuth authorize endpoint to reject the request with a duplicate scope error (`HTTP 400 invalid_request`).
   - **Fix**: Cleaned up `SCOPES` in `config.py` to name each area at most once: `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

3. **Spurious Token Expiry After 1 Hour ("expired, reconnect")**:
   - **Cause**: Intervals.icu access tokens do not expire and do not issue a `refresh_token` (they remain valid until revoked by the athlete). In `server.py`, `store_connection` fell back to a default TTL of 3600 seconds (`DEFAULT_TOKEN_TTL = 3600`) when `expires_in` was omitted in the token response. The background thread `refresh_tokens()` ran periodically, saw that `expires_at` had elapsed, found no `refresh_token` in storage, and marked the connection as `"expired, reconnect"`.
   - **Fix**: Removed the artificial 3600s expiration for tokens that have no `expires_in` or `refresh_token`. The background refresher now skips perpetual tokens, and revocation is handled lazily upon receiving an HTTP 401 on API requests (marking the connection as expired/reconnect).

4. **Token Exchange Parameters**:
   - **Cause**: In `server.py`, `exchange_code` sent `grant_type: "authorization_code"` and `redirect_uri`. Intervals.icu expects only `client_id`, `client_secret`, and `code`.
   - **Fix**: Cleaned up the parameters in `exchange_code` to send only `client_id`, `client_secret`, and `code`.
