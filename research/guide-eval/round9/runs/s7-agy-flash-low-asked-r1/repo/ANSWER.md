# Root Causes and Fixes for Intervals.icu Integration

## 1. Connect Button Fails for Everyone (Unauthorized 401)
* **Cause**: In `static/app.js`, the "Connect Intervals.icu" button was implemented as a simple navigation link (`<a href="/api/intervals/auth/init">`). Navigating via an `<a>` link initiates a standard browser document GET request, which does not send the user's `Authorization: Bearer <token>` stored in `localStorage`. As a result, `server.py` rejected the request with `401 Unauthorized` (`no Authorization header`).
* **Fix**:
  * Updated `server.py` to handle `POST /api/intervals/auth/init` by returning `{ "authorize_url": auth_url }` as JSON (while retaining GET fallback).
  * Updated `static/app.js` so clicking the Connect button issues an authenticated `POST` request via the app's `api()` helper (which attaches the `Authorization` header), and then navigates the user via `window.location.assign(res.authorize_url)`.

## 2. Invalid Request (400) on Intervals Authorize Screen (Duplicate Scopes)
* **Cause**: In `config.py`, `SCOPES` was configured as `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`. In Intervals.icu's OAuth implementation, write permissions imply read permissions (`:WRITE` implies `:READ`), and specifying both `:READ` and `:WRITE` for the same scope category causes Intervals.icu to reject the authorization request with an `invalid_request` (`Duplicate scope`) error.
* **Fix**:
  * Updated `SCOPES` in `config.py` to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` (listing each scope category at most once).

## 3. Disconnection After One Hour ("status: expired, reconnect")
* **Cause**: In `server.py`, `store_connection()` assumed all tokens expire and set an artificial 3600-second (1 hour) TTL default (`DEFAULT_TOKEN_TTL = 3600`) when `expires_in` was absent in the token response. Furthermore, Intervals.icu OAuth access tokens are perpetual (they do not provide `expires_in` or `refresh_token` and remain valid until manually revoked). The background token refresher in `server.py` checked every minute, found the token approaching expiry without a `refresh_token`, and erroneously marked the connection as `"expired, reconnect"`.
* **Fix**:
  * Updated `store_connection()` in `server.py` to only set `expires_at` if `expires_in` is actually provided by the provider.
  * Updated `refresh_tokens()` to skip token expiration for perpetual tokens (where `expires_at` is `None`).
  * Added lazy revocation handling: if a call to the Intervals.icu API fails with `401 Unauthorized`, mark the user's connection as `"expired, reconnect"` so they are prompted to reconnect only when the token has actually been revoked.
