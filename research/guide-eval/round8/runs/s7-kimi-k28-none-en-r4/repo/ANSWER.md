# Intervals.icu connection — root causes

Three independent bugs stacked on top of each other; every athlete hit #1,
and anyone who got past it hit #2, so no one could connect. Bug #3 killed the
one connection that was made by hand.

## 1. Connect button sends no credentials → 401 for everyone

- **Where:** `static/app.js` (Connect control), `server.py` `auth_init`.
- **Cause:** the Connect control was a plain `<a href="/api/intervals/auth/init">`.
  That is a full-page browser navigation, so it carries none of the request
  headers the SPA's `api()` fetch wrapper sets — in particular no
  `Authorization: Bearer <token>`. The endpoint requires that header
  (`require_user`), so every click ended on `401 {"error": "unauthorized"}`.
  Confirmed by `logs/connect-attempt.log` §1: the browser request shows no
  Authorization header, and the server logged `401 (no Authorization header)`.
- **Fix:** the button now calls `/api/intervals/auth/init` through `api()`
  (which attaches the Bearer token); the endpoint answers `200 {"url": ...}`
  and the SPA navigates the browser there. (JSON instead of the old bare 302,
  because fetch would otherwise follow the redirect cross-origin to
  intervals.icu and hit CORS.)

## 2. Authorize request missing `response_type=code` → 400 from Intervals.icu

- **Where:** `server.py` `auth_init` (authorize URL construction).
- **Cause:** the authorize URL was built without `response_type`, which
  RFC 6749 §4.1.1 makes a required parameter of the authorization-code grant.
  Intervals.icu rejects such requests with `400 {"error":"invalid_request"}`
  before the consent screen — exactly the body in
  `logs/connect-attempt.log` §2. The note there that removing/changing
  `state` or `redirect_uri` gives the same body rules those out; the missing
  parameter is `response_type`. This regressed when the calendar sync shipped
  on 2026-10-02 (the same change that added the CALENDAR scopes to the
  authorize request); the pasted-link workaround from September died with it.
- **Fix:** `auth_init` now sends `response_type=code`. The scopes in
  `config.py` are valid Intervals.icu scopes (ACTIVITY/WELLNESS/CALENDAR ×
  READ/WRITE per the provider's docs) and were not the problem.

## 3. Non-expiring Intervals.icu tokens "expire" after 1 hour → "reconnect"

- **Where:** `server.py` `store_connection` / `refresh_tokens` /
  `DEFAULT_TOKEN_TTL`.
- **Cause:** Intervals.icu token responses contain **no `expires_in` and no
  `refresh_token`** (see the 2026-09-19 response in
  `logs/connect-attempt.log` §3, which matches the provider's documented
  response shape). Its access tokens live until the athlete revokes access.
  The server instead assumed a fabricated 3600 s TTL whenever the provider
  omitted `expires_in`, and the background refresher then flipped the
  connection to `expired, reconnect` an hour later even though the token was
  still valid — which is why T. Rivera was told to reconnect the next morning
  (ticket #219).
- **Fix:** a missing `expires_in` is now stored as a non-expiring connection
  (`expires_at = None`), and the refresher skips those. A provider-reported
  `expires_in` is still honored, and the refresh-token path is kept for
  providers that issue refresh tokens.

## Verification

All against a localhost mock of the Intervals.icu API/OAuth endpoints
(documented behavior; nothing external was contacted):

- init without token → 401; init with bearer → 200 JSON URL containing
  `response_type=code` and the calendar scopes.
- authorize URL without `response_type` → 400 `invalid_request` (reproduces
  the prod failure; the fixed server no longer emits such URLs).
- full OAuth flow → callback stores the connection → `status` shows
  connected → `wellness` proxies through.
- connection still `connected` after a full refresher pass (previously it
  would read `expired, reconnect` once the fabricated TTL elapsed).
