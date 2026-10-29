# Root Causes of Intervals.icu Integration Issues

### 1. Connect button fails with 401 Unauthorized (`{"error": "unauthorized"}`)
- **Cause**: The frontend rendered the "Connect Intervals.icu" action as a direct link (`<a href="/api/intervals/auth/init">`), triggering a standard browser document navigation (GET request). In browser full-page navigations, `Authorization` headers stored in the SPA's `localStorage` (such as `Bearer tok-okafor`) are not sent. The backend endpoint `/api/intervals/auth/init` expected an authenticated session via the `Authorization` header, rejected the request without the header, and returned a 401 Unauthorized error.
- **Fix**: Switched the `/api/intervals/auth/init` endpoint to an authenticated `POST` endpoint returning JSON containing `{authorize_url: "..."}`. Updated `static/app.js` to change the connect link to a button whose click handler makes an authenticated `POST` request via the SPA fetch wrapper, then navigates to the returned URL via `window.location.assign(authorize_url)`.

### 2. Intervals.icu authorization rejects request with 400 Bad Request (`{"error": "invalid_request"}`)
- **Cause**: In `config.py`, the requested OAuth scopes were configured as `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. Intervals.icu rejects scopes that list both read and write permissions for the same area with a duplicate scope error (because `:WRITE` implies `:READ`).
- **Fix**: Cleaned up `SCOPES` in `config.py` to `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` so each area is listed at most once.

### 3. Reconnect prompt after an hour for connected athletes
- **Cause**: Intervals.icu access tokens are perpetual credentials; they do not expire on a timer and the token endpoint does not return `expires_in` or `refresh_token`. The server code assumed standard short-lived tokens and defaulted token TTL to 3600 seconds (1 hour). A background thread `refresh_tokens()` was scheduled to refresh tokens before expiry; finding no `refresh_token`, it marked the user connection as `status="expired, reconnect"` and cleared the access token after 1 hour.
- **Fix**: Removed the artificial 3600-second expiration and the periodic `refresh_tokens()` background worker. Intervals.icu tokens live indefinitely until revoked by the athlete. Handled token revocation lazily: when an API call (such as `/api/intervals/wellness`) receives a 401 from Intervals.icu, clear the access token and set status to reconnect.

### 4. Token exchange parameters
- **Cause / Optimization**: In `server.py`, `exchange_code()` sent standard OAuth parameters `grant_type="authorization_code"` and `redirect_uri` which Intervals.icu does not require on `POST /api/oauth/token`.
- **Fix**: Updated `exchange_code()` to post only `client_id`, `client_secret`, and `code`.

---

## Colleague's Note: What Applied and What Was Ignored

- **Applied**:
  - **Section 1 (Token expiration & refresh)**: Intervals.icu tokens do not return `refresh_token` or `expires_in` and do not expire after 3600s. We removed the synthetic 1-hour expiry and background token refresh thread, and implemented lazy revocation handling on HTTP 401.
  - **Section 2 ("Duplicate scope")**: Intervals.icu rejects duplicate scope areas when both `:READ` and `:WRITE` are requested. We simplified `SCOPES` to list each scope area once (`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`).
  - **Section 3 (Token exchange form fields)**: Intervals' `/api/oauth/token` expects form fields `client_id`, `client_secret`, and `code` without `grant_type` or `redirect_uri`. We updated `exchange_code()` accordingly.
  - **Section 4 (Init endpoint POST vs GET)**: Full-page navigation drops the SPA's `Authorization: Bearer` header. Changed `/api/intervals/auth/init` to authenticated POST returning `{authorize_url}` and updated the SPA button click handler to fetch and redirect via `window.location.assign`.

- **Ignored / Not Applicable**:
  - **Custom JWT signing / purpose claim / TTL rewrite for state**: The existing state parameter implementation using HMAC-SHA256 (`sign_state` and `verify_state`) with a 15-minute (900s) TTL already securely bound the user ID across the OAuth redirect without needing replacement by an external JWT library.
  - **Encrypted token storage at rest**: Production encryption at rest was mentioned as advice for persistent storage, but this in-memory dev implementation (`server.py`) stores runtime connections in memory as specified by the repository architecture.
  - **Account mismatch guard on reconnect**: The codebase did not implement multi-account linking checks or store previous athlete IDs across reconnects, so no account-mismatch check was needed.
