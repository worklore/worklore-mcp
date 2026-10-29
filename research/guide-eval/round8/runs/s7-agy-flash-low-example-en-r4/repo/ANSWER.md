# Root Causes and Fixes for Intervals.icu Integration Issues

## Summary of Root Causes

1. **Connect Button 401 Unauthorized (`/api/intervals/auth/init`)**:
   - **Cause**: The "Connect Intervals.icu" button was implemented in the frontend as a plain link `<a href="/api/intervals/auth/init">`. Full-page document navigations in a browser do not attach the SPA's `Authorization: Bearer <token>` stored in `localStorage`. The backend endpoint expected an authenticated user via `Authorization` header, immediately returning `401 Unauthorized`.
   - **Fix**: Changed `/api/intervals/auth/init` on the backend to accept authenticated `POST` requests and return the generated authorize URL as JSON (`{"authorize_url": ...}`). Updated the frontend (`app.js`) to use a `<button>` that issues an authenticated `api("/api/intervals/auth/init", { method: "POST" })` fetch call and navigates via `window.location.assign(res.authorize_url)`.

2. **Invalid Request / 400 on Intervals.icu Consent Screen**:
   - **Cause**: `config.SCOPES` requested duplicated scopes (`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`). Intervals.icu does not allow requesting both `:READ` and `:WRITE` permissions for the same area because `:WRITE` implies `:READ`. Specifying both triggers an authorization failure on Intervals.icu.
   - **Fix**: Cleaned up the scope list to name each area at most once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **Athlete Connection Marked "Expired, reconnect" After 1 Hour**:
   - **Cause**: Intervals.icu OAuth tokens do not expire and do not issue refresh tokens (`refresh_token` and `expires_in` are not provided in the token exchange response). The backend defaulted token TTL to 3600 seconds (1 hour) and ran a background loop `refresh_tokens()` that attempted to refresh the token after an hour. Since there was no `refresh_token`, the refresher automatically marked the connection as `"expired, reconnect"`.
   - **Fix**: Removed artificial token expiry and the background `refresh_tokens()` loop. Access tokens are kept valid indefinitely and handled lazily: when an API request to Intervals.icu (such as `/wellness`) returns a `401 Unauthorized` (indicating the athlete revoked access), the stored token is invalidated and the status is transitioned to `"expired, reconnect"`.

4. **Extraneous Parameters in Token Exchange**:
   - **Cause**: `exchange_code()` sent standard OAuth parameters `grant_type="authorization_code"` and `redirect_uri` in addition to `code`, `client_id`, and `client_secret`.
   - **Fix**: Trimmed the POST parameters in `exchange_code()` to send only `client_id`, `client_secret`, and `code`.

---

## Applicability of the Colleague's Note

- **Applied**:
  - **Point 1 (Token never expires, no refresh token, lazy revocation on 401)**: Fully applied. Removed the 1-hour expiry assumption and background refresher loop, which caused Rivera's account to disconnect after an hour. Implemented lazy revocation by checking for 401 responses in Intervals API requests.
  - **Point 2 ("Duplicate scope")**: Fully applied. Deduplicated scopes in `config.py` from `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE` down to `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
  - **Point 3 (Token exchange standard-lite)**: Fully applied. Simplified `exchange_code` to send only `client_id`, `client_secret`, and `code`.
  - **Point 4 (Init endpoint must be POST)**: Fully applied. Converted `/api/intervals/auth/init` from GET document redirect to authenticated POST returning `{authorize_url}`, and triggered navigation via `window.location.assign(...)` in the SPA.

- **Did Not Apply / Ignored**:
  - **Signed JWT for state**: The codebase already used a working HMAC-SHA256 signature scheme (`sign_state` and `verify_state`) that securely carries the `user_id` and timestamp across the OAuth redirect flow without adding extra external dependencies.
  - **Token encryption at rest**: The current service architecture keeps sessions and credentials in memory (matching the dev stub environment in `server.py`). Database encryption at rest is relevant to production persistent storage rather than the in-memory backend stub.
  - **Account-mismatch guard on reconnect**: Not part of the reported bug issues or existing connection handling logic.
