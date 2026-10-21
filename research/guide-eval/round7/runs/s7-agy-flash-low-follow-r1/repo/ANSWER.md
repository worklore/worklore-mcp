# Causes of Intervals.icu Integration Issues

### 1. Connect button 401 Unauthorized for everyone
* **Cause**: The frontend rendered "Connect Intervals.icu" as a plain link `<a href="/api/intervals/auth/init">`. Clicking the link triggered full-page document navigation (GET request), which does not send the user's `Authorization: Bearer <token>` stored in `localStorage`. Because `server.py` required authentication on `/api/intervals/auth/init`, every direct GET navigation was rejected with `401 Unauthorized`.
* **Fix**: Changed `/api/intervals/auth/init` to an authenticated `POST` endpoint that returns `{authorize_url}` as JSON. Updated the frontend to send an authenticated `POST` via the SPA's `api()` fetch wrapper and navigate via `window.location.assign(authorize_url)`.

### 2. Manual URL / Authorize step failing with HTTP 400 (`Duplicate scope`)
* **Cause**: In `config.py`, `SCOPES` was configured as `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`. On Intervals.icu, `:WRITE` implies `:READ`. Requesting both `:READ` and `:WRITE` for the same area triggers a `Duplicate scope` error (`invalid_request`).
* **Fix**: Cleaned up the scope list so each area is specified at most once: `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

### 3. Premature token expiration and reconnection prompt after 1 hour
* **Cause**: Intervals.icu tokens do not expire and do not issue a `refresh_token`. The server previously assumed tokens without a `refresh_token` expire after a default TTL of 3600 seconds (`DEFAULT_TOKEN_TTL`), and the background token refresher thread `refresh_tokens()` marked the connection as `"expired, reconnect"` once the hour elapsed.
* **Fix**: Removed the synthetic 1-hour expiration, removed the token refresher loop, and handled revocation lazily: on a 401 response from the Intervals.icu API, clear the stored access token and mark the status as `"expired, reconnect"`.

### 4. Token exchange parameters & Callback security
* **Cause**:
  - The token exchange endpoint on Intervals.icu (`POST /api/oauth/token`) expects form fields `client_id`, `client_secret`, and `code` only (no `grant_type` or `redirect_uri`).
  - The OAuth `state` parameter previously used a simple colon-separated timestamp hash instead of a signed JWT with `sub`, `purpose`, and TTL claims.
  - Reconnection did not enforce account matching to prevent an athlete from accidentally linking a different Intervals.icu account.
* **Fix**: Updated `exchange_code()` to post only `client_id`, `client_secret`, and `code`; implemented a signed JWT `state` (`sub`, `purpose: "intervals_oauth"`, 15-minute TTL); and added an account-mismatch check rejecting callbacks if the incoming athlete ID does not match an existing connection for that user.
