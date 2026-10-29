# Root Causes & Applied Notes

## 1. Root Causes of Connection Failures

1. **Connect Button 401 Unauthorized (`/api/intervals/auth/init` was GET)**
   - The Connect button in `static/app.js` was a standard HTML link (`<a href="/api/intervals/auth/init">`), triggering a full-page browser navigation (`GET`).
   - Browser page navigations do not send the `Authorization: Bearer <token>` stored in `localStorage`.
   - As a result, the server's `require_user()` check rejected every athlete click with HTTP 401 Unauthorized.

2. **OAuth Authorization Rejection ("Duplicate scope" / `invalid_request`)**
   - In `config.py`, `SCOPES` was configured as:
     `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`
   - Intervals.icu enforces that `:WRITE` implies `:READ`, and each permission area can be named at most once. Specifying both `:READ` and `:WRITE` for the same area triggers an authorization error (`invalid_request` / `Duplicate scope`).

3. **Athlete Told to Reconnect After 1 Hour (Artificial Expiry & Token Refresh Assumption)**
   - Intervals.icu OAuth access tokens do not expire and the token response includes neither `expires_in` nor `refresh_token`.
   - `server.py` had a fallback `DEFAULT_TOKEN_TTL = 3600` seconds (1 hour). When no `refresh_token` was returned, it scheduled an expiry in 3600s.
   - A background thread `refresh_tokens()` ran periodically. Once 3600s passed, it found no `refresh_token` and marked the user status as `"expired, reconnect"` and cleared `access_token`.

4. **Token Exchange Parameters (`POST /api/oauth/token`)**
   - `server.py` passed `grant_type: "authorization_code"` and `redirect_uri` during token exchange. Intervals.icu's token endpoint expects only `client_id`, `client_secret`, and `code`.

---

## 2. Colleague's Note: What Applied and What Was Ignored

### Parts that applied:
- **Point 1 (Token never expires, no refresh_token; handle lazily on 401):**
  - Applied. Removed `DEFAULT_TOKEN_TTL`, the scheduled expiry, and the background refresh thread `refresh_tokens()`. Updated `intervals_get()` to lazily handle HTTP 401 responses by setting the connection status to `"expired, reconnect"` and clearing `access_token`.
- **Point 2 ("Duplicate scope"):**
  - Applied. Cleaned `config.SCOPES` to name each area at most once (`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`), omitting `:READ` when `:WRITE` is specified.
- **Point 3 (Token exchange standard-lite):**
  - Applied. Updated `exchange_code()` to send only form fields `client_id`, `client_secret`, and `code`, removing `grant_type` and `redirect_uri`.
- **Point 4 (Init endpoint must be POST):**
  - Applied. Changed `/api/intervals/auth/init` on the server from `GET` (which redirected) to an authenticated `POST` returning `{"authorize_url": auth_url}`. In `static/app.js`, changed the Connect link to a button that calls `api("/api/intervals/auth/init", { method: "POST" })` and navigates using `window.location.assign(res.authorize_url)`.

### Parts that were ignored / did not apply:
- **State parameter JWT signing and account-mismatch guard:**
  - `server.py` already had HMAC-SHA256 signature and timestamp validation for `state` (`sign_state` and `verify_state`). Replacing this with JWT and adding athlete ID mismatch verification was not needed for fixing the integration issues and was outside the scope of the fix.
- **Token encryption at rest:**
  - `server.py` is an in-memory implementation for development and testing as noted in `README.md`. Encrypting tokens in memory was ignored as it does not apply to the in-memory dev server.
