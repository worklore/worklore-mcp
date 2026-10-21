# Intervals.icu OAuth Integration Fixes

## Summary of Root Causes

1. **Connect Button 401 Unauthorized for All Users (`auth/init` as GET)**:
   The frontend SPA was rendering `<a href="/api/intervals/auth/init">Connect Intervals.icu</a>`. Clicking a standard anchor tag triggers a full document navigation in the browser. Browser document navigations do not send the custom `Authorization: Bearer <token>` header stored in `localStorage`, resulting in `server.py` returning `401 Unauthorized` for every user attempting to connect.

2. **400 Invalid Request / "Duplicate Scope" on Authorization URL**:
   `config.py` requested `SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`. On Intervals.icu, `:WRITE` permissions imply `:READ`. Specifying both `:READ` and `:WRITE` for the same scope namespace (such as `ACTIVITY` or `CALENDAR`) triggers a duplicate scope error (`invalid_request`), which prevented users from seeing the OAuth consent screen.

3. **Reconnection Forced After 1 Hour (Token Expiry & Refresh Background Thread)**:
   Intervals.icu access tokens do not expire and do not issue a `refresh_token`. The backend defaulted missing `expires_in` values to 3600 seconds (1 hour) and ran a background loop (`refresh_tokens()`) checking for expiring tokens. When the 1-hour timer elapsed, because no `refresh_token` existed on file, the background job unilaterally marked the connection as `"expired, reconnect"` and cleared the token.

4. **Non-Standard Token Exchange Parameters**:
   The token exchange helper in `server.py` passed `grant_type="authorization_code"` and `redirect_uri` to `POST https://intervals.icu/api/oauth/token`, whereas Intervals.icu's token endpoint expects only `client_id`, `client_secret`, and `code`.

---

## Analysis of Colleague's Note: What Applied vs. What Was Ignored

| Colleague's Note Item | Applied / Ignored | Details |
|---|---|---|
| **1. Token lifetime & lazy revocation** | **Applied** | Intervals.icu access tokens do not include `refresh_token` or `expires_in`. We removed the artificial 1-hour expiry and background token refresh worker. We implemented lazy revocation handling: if a call to the Intervals.icu API returns HTTP 401, the stored token is cleared and the connection status is set to `"expired, reconnect"`. |
| **2. "Duplicate scope" rule** | **Applied** | Updated `SCOPES` in [config.py](file:///tmp/h-O7FlzT/config.py) from `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE` to `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` so each functional domain is specified only once. |
| **3. Token exchange parameters** | **Applied** | Streamlined `exchange_code()` in [server.py](file:///tmp/h-O7FlzT/server.py) to send only `client_id`, `client_secret`, and `code` to `POST /api/oauth/token`. |
| **4. POST `/auth/init` endpoint & SPA fetch** | **Applied** | Changed `/api/intervals/auth/init` from `GET` to `POST` returning JSON `{ "authorize_url": ... }`. Updated [static/app.js](file:///tmp/h-O7FlzT/static/app.js) to trigger `POST /api/intervals/auth/init` via the authenticated `api()` fetch wrapper and redirect via `window.location.assign(res.authorize_url)`. |
| **State parameter signing & JWT suggestions** | **Partially Applied / Kept Existing** | The codebase already had a working HMAC-signed state parameter mechanism (`sign_state` / `verify_state` with timestamp verification and 15-minute TTL); existing state verification logic was maintained without replacing it with external JWT libraries. |
| **Database token encryption at rest** | **Ignored** | The current application is a local stdlib-only in-memory reference implementation without encrypted database storage. |
| **Account mismatch guard** | **Ignored / Not needed** | The multi-tenant account mismatch guard mentioned in the note was not part of the required codebase architecture. |
