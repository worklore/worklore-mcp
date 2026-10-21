# Causes of the Intervals.icu Connection Issues

### 1. Connect Button 401 Unauthorized Error
- **Cause**: The "Connect Intervals.icu" button in `static/app.js` was implemented as a simple document navigation link (`<a class="btn" href="/api/intervals/auth/init">`). In the tricoach SPA, the user authentication token resides in browser `localStorage` and is attached to fetch requests via the `Authorization: Bearer` header. Clicking the link triggered a standard browser GET request that omitted the `Authorization` header, causing `require_user()` in `server.py` to reject the request with HTTP 401 `{"error": "unauthorized"}`.
- **Fix**: The frontend was updated to append the user token as a query parameter (`/api/intervals/auth/init?token=...`), and `server.py` was updated so `current_user()` checks for the token in the query string as well as the `Authorization` header.

### 2. Missing `response_type=code` in OAuth Authorization Request
- **Cause**: In `server.py` (`auth_init`), the parameters passed when constructing the redirect URL to `https://intervals.icu/oauth/authorize` did not include `response_type=code`. Per RFC 6749 (Section 4.1.1), `response_type` is required for authorization code grant requests. Intervals.icu returned HTTP 400 `{"error": "invalid_request"}` whenever the authorize URL was accessed (which was previously misattributed to the `CALENDAR` scopes).
- **Fix**: Added `"response_type": "code"` to the query parameters in `auth_init()`.

### 3. Premature Expiration and "expired, reconnect" After 1 Hour
- **Cause**: Intervals.icu issues long-lived OAuth access tokens and does not return `expires_in` or `refresh_token` in its token response. `server.py` incorrectly fell back to `DEFAULT_TOKEN_TTL = 3600` (1 hour) when `expires_in` was absent. After ~55 minutes, the background refresher loop `refresh_tokens()` detected that the connection was within 300 seconds of expiry. Because no `refresh_token` existed, it marked the status as `"expired, reconnect"` and nullified the valid access token.
- **Fix**: Updated `store_connection()` to only set `expires_at` when `expires_in` is explicitly provided by the OAuth response (leaving it `None` for non-expiring tokens), and updated `refresh_tokens()` so it skips connections without an `expires_at` timestamp.
