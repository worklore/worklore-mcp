# Root Causes for Intervals.icu Integration Issues

Three distinct issues caused the connection problems reported by athletes:

## 1. Connect button failed for everyone with 401 Unauthorized
- **Cause**: The frontend rendered the "Connect Intervals.icu" button as a direct navigation link (`<a href="/api/intervals/auth/init">`). In the SPA architecture, user authentication tokens are stored in `localStorage` and dispatched via `Authorization: Bearer <token>` HTTP request headers on `fetch()` calls. A browser's full-page link navigation does not attach custom `Authorization` headers, causing the backend's `require_user()` check to fail and return `401 Unauthorized`.
- **Fix**: Updated `/api/intervals/auth/init` on the backend to handle authenticated `POST` requests and return `{ "authorize_url": ... }` as JSON. Updated the frontend SPA (`app.js`) to trigger an authenticated `api("/api/intervals/auth/init", { method: "POST" })` call when the Connect button is clicked and navigate using `window.location.assign(res.authorize_url)`.

## 2. Intervals.icu rejected authorization requests with HTTP 400 `invalid_request`
- **Cause**: The OAuth configuration requested overlapping scopes (`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`). In Intervals.icu's OAuth implementation, write permissions (e.g., `:WRITE`) implicitly grant read access, and including both `:READ` and `:WRITE` for the same domain causes a duplicate scope error, triggering an HTTP 400 `invalid_request`.
- **Fix**: Updated `SCOPES` in `config.py` to deduplicate domain permissions to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. Disconnection after 1 hour ("Status: expired, reconnect")
- **Cause**: Intervals.icu OAuth access tokens are long-lived and do not return an `expires_in` or `refresh_token` field in the token exchange response. The backend assumed a `DEFAULT_TOKEN_TTL = 3600` (1 hour) when `expires_in` was missing, and the background task `refresh_tokens()` subsequently marked the connection as `"expired, reconnect"` when no refresh token was found after 1 hour.
- **Fix**: Updated `store_connection` to avoid assigning an artificial 1-hour expiration timestamp to Intervals.icu connections. Updated `refresh_tokens()` to avoid expiring connections that do not provide or require refresh tokens. Revocation is instead handled lazily if an API call (e.g. `/wellness`) returns an HTTP 401.
