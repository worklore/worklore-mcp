# Intervals.icu Integration Issues and Root Causes

## 1. Connect button fails with 401 Unauthorized for everyone
* **Cause**: In `static/app.js`, the "Connect Intervals.icu" button was implemented as a standard anchor link (`<a href="/api/intervals/auth/init">`). Clicking this link performed full-page browser navigation to a `GET` endpoint. Full-page navigations do not send the tricoach authentication token stored in `localStorage` (`Authorization: Bearer <token>`). As a result, `server.py` rejected the unauthenticated request with a `401 Unauthorized` response.
* **Fix**: Converted `POST /api/intervals/auth/init` to an authenticated endpoint returning `{"authorize_url": ...}` as JSON. Changed the frontend to send an authenticated `POST` request via the `api()` fetch wrapper and redirect using `window.location.assign(authorize_url)`.

## 2. Authorization link rejected with HTTP 400 (`invalid_request` / Duplicate Scope)
* **Cause**: In `config.py`, `SCOPES` was configured with duplicate permissions for the same areas: `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`. On Intervals.icu, write access (`:WRITE`) implicitly includes read access (`:READ`), and requesting both scopes for the same area causes Intervals.icu's OAuth authorize endpoint to reject the request with HTTP 400.
* **Fix**: Removed redundant `:READ` scopes from `config.py`, updating `SCOPES` to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. Disconnection after one hour ("Status: expired, reconnect")
* **Cause**: Intervals.icu access tokens do not expire and do not issue a `refresh_token`. The backend defaulted token TTL to 3600 seconds (`DEFAULT_TOKEN_TTL = 3600`) and ran a background refresher thread (`refresh_tokens`). After 3600 seconds, because no `refresh_token` existed in the stored connection, the background job forcibly marked the user's connection status as `"expired, reconnect"` and cleared the access token.
* **Fix**: Disabled the artificial token expiration timer and background expiry check for Intervals.icu connections. Tokens persist indefinitely until revoked, and token invalidation is handled lazily if Intervals.icu returns an HTTP 401 on API requests.

## 4. Token exchange parameters
* **Cause**: In `exchange_code()`, the token endpoint request included extra fields (`grant_type: authorization_code` and `redirect_uri`) which deviate from Intervals.icu's OAuth token endpoint requirements (`client_id`, `client_secret`, and `code` only).
* **Fix**: Streamlined the token exchange request payload in `exchange_code()` to include only `client_id`, `client_secret`, and `code`.
