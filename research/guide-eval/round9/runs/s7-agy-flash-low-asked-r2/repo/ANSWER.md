# Causes of Intervals.icu Connection Failures

### 1. Connect Button Returning `{"error": "unauthorized"}` (401)
* **Cause**: The frontend rendered the "Connect Intervals.icu" button as a standard link `<a href="/api/intervals/auth/init">`. Full-page document navigation in a browser does not pass the custom `Authorization: Bearer <token>` header stored in `localStorage`. Because `/api/intervals/auth/init` requires authentication (`require_user()`), the server received requests with no `Authorization` header and returned HTTP 401 Unauthorized.
* **Fix**: Changed `/api/intervals/auth/init` to an authenticated `POST` endpoint that returns JSON containing `{ "authorize_url": ... }`. Updated the frontend `static/app.js` to call this endpoint via its authenticated `api()` fetch wrapper, then redirect via `window.location.assign(data.authorize_url)`.

### 2. Intervals.icu Authorize Endpoint Returning `{"error": "invalid_request"}` (400)
* **Cause**: Intervals.icu rejects duplicate scope areas (such as requesting both `:READ` and `:WRITE` for the same area, e.g. `ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE`). In Intervals.icu's OAuth implementation, `:WRITE` implicitly includes `:READ`. Requesting both for the same resource causes Intervals.icu to reject the authorization request with an error.
* **Fix**: Cleaned up `SCOPES` in `config.py` to specify each area at most once without redundant read scopes (`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`).

### 3. Connection Expiring After 1 Hour ("Status: expired, reconnect")
* **Cause**: Intervals.icu OAuth access tokens do not expire and the token exchange response does not include an `expires_in` or `refresh_token` field. The backend server fell back to a default TTL of 3600 seconds (`DEFAULT_TOKEN_TTL = 3600`) and scheduled expiry for 1 hour later. When the background refresher ran, it found `expires_at` had passed and no `refresh_token` existed, incorrectly marking the connection as `"expired, reconnect"` and clearing the token.
* **Fix**:
  - In `store_connection()`, only set `expires_at` if `expires_in` is explicitly provided by the provider; otherwise treat the token as perpetual.
  - In `refresh_tokens()`, ignore connections where `expires_at` is not set.
  - Handle token invalidation/revocation lazily on API calls in `intervals_get()`: if Intervals returns HTTP 401, clear the access token and update status to `"expired, reconnect"`.
  - Streamlined token exchange parameters in `exchange_code()` to send `client_id`, `client_secret`, and `code`.
