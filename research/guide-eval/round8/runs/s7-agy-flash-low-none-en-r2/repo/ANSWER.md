# Root Causes of Intervals.icu Integration Failures

The integration failed due to three separate issues:

### 1. Direct Browser Navigation to Auth Init Stripped the Authorization Header (`401 Unauthorized`)
- **Cause**: The "Connect Intervals.icu" button was implemented as a plain HTML link (`<a href="/api/intervals/auth/init">`). When clicked, standard full-page browser document navigation does not send the client-side session token stored in `localStorage` (`tok-okafor` / `Authorization: Bearer <token>`). The server's `require_user()` check failed, returning `401 Unauthorized` for every athlete clicking the button.
- **Fix**: Supported `POST /api/intervals/auth/init` returning JSON with `{ "authorize_url": ... }`, and updated the SPA (`static/app.js`) to invoke it via the authenticated `api()` fetch wrapper before navigating to the returned authorization URL via `window.location.assign(authorize_url)`.

### 2. Overlapping / Redundant OAuth Scopes (`invalid_request` / `Duplicate scope`)
- **Cause**: In `config.py`, `SCOPES` requested both read and write scopes for the same areas: `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. In Intervals.icu's OAuth 2.0 implementation, `:WRITE` permissions implicitly include `:READ` permissions. Specifying both permissions for the same resource area violates strict scope validation, returning a `400 invalid_request` (`Duplicate scope`) on the `/oauth/authorize` endpoint.
- **Fix**: Deduplicated the scopes in `config.py` to only request the highest privilege required for each area: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

### 3. Faulty Token Refresh Machinery and Artificial Token Expiration
- **Cause**: Intervals.icu OAuth access tokens are perpetual credentials; they do not expire automatically and the token response does not return a `refresh_token` or `expires_in`. In `server.py`, the backend defaulted missing `expires_in` values to `DEFAULT_TOKEN_TTL = 3600` (1 hour) and ran a background worker `refresh_tokens()`. When the 1-hour window lapsed and no `refresh_token` was present, the worker forcibly marked the connection as `"expired, reconnect"` and cleared the athlete's `access_token`. Furthermore, `exchange_code` unnecessarily passed `grant_type="authorization_code"` and `redirect_uri` which are not part of Intervals' minimal token exchange schema.
- **Fix**:
  - Removed the artificial 3600-second expiration and the periodic `refresh_tokens()` worker thread.
  - Minimalized `exchange_code()` to post only `client_id`, `client_secret`, and `code`.
  - Implemented lazy token revocation handling: if an Intervals.icu API request returns `401 Unauthorized` (indicating the athlete revoked access in Intervals.icu), the integration marks the connection as `"expired, reconnect"`.
