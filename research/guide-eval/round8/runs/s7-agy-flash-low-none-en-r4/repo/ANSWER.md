# Causes of Intervals.icu Integration Issues

### 1. Connect button failed with 401 Unauthorized (`{"error": "unauthorized"}`)
* **Cause**: In `static/app.js`, the "Connect Intervals.icu" button was a direct browser hyperlink (`<a href="/api/intervals/auth/init">`). When clicked, the browser navigated directly to the endpoint without sending the user's `tc_token` from `localStorage` in the `Authorization: Bearer` header. The backend required authentication on `/api/intervals/auth/init` via `require_user()`, which inspected only the `Authorization` request header, rejecting the browser navigation with HTTP 401.
* **Fix**: Updated `static/app.js` to append the user token as a query parameter (`/api/intervals/auth/init?token=...`), and updated `server.py` to allow `current_user()` to authenticate requests via either the `Authorization: Bearer` header or the query parameter.

### 2. Intervals.icu returned HTTP 400 `{"error":"invalid_request"}` on Authorization
* **Cause**: In `config.py`, `SCOPES` was configured as `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`. On Intervals.icu, write permissions imply read permissions for each scope domain (`:WRITE` includes read access). Requesting duplicate permission categories (both `:READ` and `:WRITE` for `ACTIVITY` and `CALENDAR`) triggers Intervals.icu's OAuth validation rejection (`invalid_request` / duplicate scope).
* **Fix**: Reduced `SCOPES` in `config.py` to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

### 3. Connection expired after 1 hour ("Status: expired, reconnect")
* **Cause**: Intervals.icu issues long-lived OAuth access tokens without a `refresh_token` or an `expires_in` attribute in the token response. `server.py` defaulted `DEFAULT_TOKEN_TTL = 3600` (1 hour) when `expires_in` was absent. After 3600 seconds, the background thread `refresh_tokens()` saw that the token had expired and that there was no `refresh_token` available, incorrectly marking the connection as `"expired, reconnect"` and wiping the valid access token.
* **Fix**: Changed `DEFAULT_TOKEN_TTL` to `None` in `server.py` and updated `store_connection` and `refresh_tokens` so that tokens lacking an `expires_in` lifetime are treated as non-expiring rather than forced into an artificial 1-hour expiration and refresh failure.
