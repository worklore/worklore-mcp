# Root Causes and Applied Fixes

## 1. Root Causes

### Cause 1: Init endpoint was a `GET` full-page link dropping authorization
- **Symptom**: Clicking "Connect Intervals.icu" immediately failed with `401 Unauthorized` (`{"error": "unauthorized"}`) for all signed-in athletes.
- **Reason**: The SPA kept the user's tricoach session token in `localStorage`, sent only via HTTP `Authorization: Bearer <token>` headers in fetch requests. The connect button was implemented as a simple HTML anchor tag (`<a href="/api/intervals/auth/init">`), triggering a full browser document navigation. Standard browser document navigations do not send custom `Authorization` headers from `localStorage`, causing the backend's `require_user()` check to fail with a 401.

### Cause 2: Scope string included duplicate areas (`ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE`)
- **Symptom**: When athletes attempted to open the authorize URL directly or via manual links, Intervals.icu returned `HTTP 400 {"error": "invalid_request"}` before displaying any consent screen.
- **Reason**: In Intervals.icu OAuth, `:WRITE` implies `:READ`. Naming the same area more than once (such as `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`) violates Intervals' rule that each area may be listed at most once, resulting in a duplicate scope error.

### Cause 3: Erroneous token expiration handling and background refresh loop
- **Symptom**: Athletes who successfully connected (e.g., T. Rivera on 2026-09-19) were marked "Status: expired, reconnect" approximately one hour later.
- **Reason**: Intervals.icu OAuth access tokens never expire and do not provide a `refresh_token` or `expires_in` in the token exchange response. The backend assumed standard OAuth token expiration (`DEFAULT_TOKEN_TTL = 3600`) when `expires_in` was missing, and ran a background refresher thread (`refresh_tokens`). Because no refresh token existed, once the 3600s timer elapsed the background refresher forcibly set the connection status to `"expired, reconnect"` and cleared the access token.

---

## 2. Note Applicability

Reviewing the colleague's note sections:

- **Section 1 (Token never expires, no refresh_token, lazy 401 revocation handling)**: **APPLIED**
  - Intervals tokens do not expire or refresh.
  - Removed the premature 3600-second expiration and background token refresh thread that expired athlete connections after an hour.
  - Implemented lazy revocation handling: if Intervals returns a `401 Unauthorized` on API calls (such as `/wellness`), the stored access token is cleared and the status is transitioned to `"expired, reconnect"`.
- **Section 2 (`"Duplicate scope"`)**: **APPLIED**
  - Intervals requires each area at most once.
  - Updated `SCOPES` in [config.py](file:///tmp/h-xZ1V46/config.py) from `"ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"` to `"ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.
- **Section 3 (Token exchange standard-lite)**: **APPLIED**
  - Intervals' `POST /api/oauth/token` expects form fields `client_id`, `client_secret`, and `code` without `grant_type` or `redirect_uri`.
  - Updated `exchange_code()` in [server.py](file:///tmp/h-xZ1V46/server.py) to post only `client_id`, `client_secret`, and `code`.
- **Section 4 & Steps (Init endpoint as authenticated `POST` returning `{authorize_url}`)**: **APPLIED**
  - Changed `/api/intervals/auth/init` from `GET` to an authenticated `POST` endpoint returning JSON `{"authorize_url": "..."}`.
  - Updated [static/app.js](file:///tmp/h-xZ1V46/static/app.js) to trigger a `POST` request with the athlete's `Authorization` header, then redirect using `window.location.assign(res.authorize_url)`.
- **Note elements not applicable or already satisfied**:
  - Signed JWT state parameter implementation: The backend already had a working signed HMAC/timestamp state implementation (`sign_state` and `verify_state`) with a 15-minute TTL.
  - Encryption at rest: As noted in the codebase, `server.py` is an in-memory test/dev implementation using dictionaries representing Postgres table shapes.
