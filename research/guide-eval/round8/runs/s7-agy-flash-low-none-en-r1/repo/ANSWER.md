# Causes and Fixes for Intervals.icu Integration Issues

## Summary of Causes

### 1. Connect button 401 Unauthorized for all athletes (`static/app.js` & `server.py`)
- **Cause**: In the Single Page Application (`static/app.js`), the "Connect Intervals.icu" link was a standard HTML anchor tag `<a href="/api/intervals/auth/init">`. When an athlete clicked it, the browser navigated directly to `/api/intervals/auth/init` via top-level document navigation. In tricoach, user authentication is stored in browser `localStorage` and sent in the `Authorization: Bearer <token>` header by the SPA's `api()` fetch wrapper. A standard anchor click does not pass custom `Authorization` headers, causing the backend endpoint (`require_user()`) to reject the request with `401 Unauthorized`.
- **Fix**: Updated `static/app.js` to handle the connect action via JavaScript click handler using the `api()` wrapper. The fetch request includes the `Authorization` header and queries `/api/intervals/auth/init`. Updated `server.py` so `/api/intervals/auth/init` detects JSON API requests and responds with `{"url": target}`, allowing the SPA to redirect via `window.location.href = data.url` (while maintaining 302 redirect fallback for standard navigation).

### 2. OAuth authorize endpoint returning `400 Bad Request: {"error": "invalid_request"}` (`config.py`)
- **Cause**: Intervals.icu OAuth rejects duplicate scopes within the same domain because `:WRITE` permissions inherently subsume `:READ` permissions. The scopes in `config.py` were configured as:
  `SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`
  Requesting both `ACTIVITY:READ` and `ACTIVITY:WRITE`, as well as `CALENDAR:READ` and `CALENDAR:WRITE`, violated Intervals.icu's duplicate scope policy and caused `/oauth/authorize` to fail immediately with `400 Bad Request` (`{"error":"invalid_request"}`).
- **Fix**: Simplified `config.py` scopes to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

### 3. Active athlete connection marked "expired, reconnect" after one hour (`server.py`)
- **Cause**: Intervals.icu OAuth access tokens are perpetual tokens that do not expire unless explicitly revoked by the athlete in Intervals.icu settings. Therefore, Intervals.icu token responses do not include an `expires_in` or `refresh_token` field. However, `server.py` assigned a fallback `DEFAULT_TOKEN_TTL = 3600` (1 hour) when `expires_in` was missing (`store_connection()`), and the background `refresh_tokens()` worker marked any connection whose `expires_at` was reached as `"expired, reconnect"` if no refresh token was present. This prematurely invalidated T. Rivera's connection 1 hour after linking.
- **Fix**: Updated `store_connection()` and `refresh_tokens()` in `server.py` so tokens without an explicit `expires_in` are treated as non-expiring (`expires_at = None`), preventing them from being falsely expired by the background refresh task.
