# Intervals.icu Integration Fixes & Root Cause Analysis

## Root Causes of Failures

1. **Connect Button 401 Unauthorized for Everyone (`/api/intervals/auth/init`)**:
   - The frontend used an HTML link `<a href="/api/intervals/auth/init">` to initiate OAuth. Full-page browser navigation does not include the `Authorization: Bearer <token>` header stored in the SPA's `localStorage`.
   - As a result, the server's `require_user()` check failed with HTTP 401.

2. **Manual OAuth URL Failure (HTTP 400 `invalid_request` from Intervals.icu)**:
   - When attempting to initiate authorization directly with the configured scopes, Intervals.icu rejected the request because the scope string in `config.py` included duplicated scope areas: `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
   - In Intervals.icu OAuth, `:WRITE` implies `:READ`, and specifying the same area twice triggers a duplicate scope error (HTTP 400).

3. **Athlete Disconnected After One Hour ("Status: expired, reconnect")**:
   - Intervals.icu access tokens do not expire and do not issue a `refresh_token` or `expires_in`.
   - The backend assumed a default TTL of 3600 seconds (`DEFAULT_TOKEN_TTL = 3600`) when `expires_in` was missing, and ran a background thread (`refresh_tokens`) that checked for expiring tokens. Because no `refresh_token` was present, the background job marked the token as `"expired, reconnect"` after one hour.

---

## Application of Colleague's Note

- **Point 1 (Token never expires, no refresh_token, handle lazy revocation on 401)**:
  - **Applied**: Removed the default 1-hour expiry assumption and the background `refresh_tokens` loop. Added lazy token invalidation on 401 responses from Intervals.icu in `/api/intervals/wellness`.

- **Point 2 (`"Duplicate scope"`)**:
  - **Applied**: Updated `config.SCOPES` from `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"` to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` so each area is listed at most once with write permissions covering reads.

- **Point 3 (Token exchange standard-lite)**:
  - **Applied**: Simplified `exchange_code()` in `server.py` to send only `client_id`, `client_secret`, and `code`, removing unnecessary standard OAuth parameters (`grant_type` and `redirect_uri`).

- **Point 4 (Init endpoint must be POST returning `{authorize_url}`, account mismatch guard)**:
  - **Applied**: Changed `/api/intervals/auth/init` from `GET` to an authenticated `POST` endpoint returning `{"authorize_url": ...}` as JSON. Updated the frontend button to trigger a `POST` request with the `Authorization` header and perform `window.location.assign(res.authorize_url)`. Added an athlete ID mismatch check on reconnection in `store_connection`.
  - **Ignored / Not Applied**: The existing HMAC-SHA256 signed `state` implementation in `server.py` already safely carried and verified identity across redirects, so migrating `state` to an external JWT library was not required. Encrypted storage at rest was not applied as the current service operates on an in-memory dev datastore.
