# Intervals.icu connection: causes

## 1. Connect button returns 401 for everyone (support #214)

The button was a plain `<a href="/api/intervals/auth/init">`. A link navigation
does not send the `Authorization: Bearer` header. The SPA only adds that header
in its `fetch` wrapper, and the token lives in `localStorage`. So the server
saw no credentials and answered `401 {"error": "unauthorized"}`, the page
athletes reported.

**Fix:** `auth_init` now returns `{"url": ...}` as JSON. The Connect button in
`static/app.js` fetches that with the token, then sets `window.location` to the
Intervals consent URL.

## 2. Authorize step answers 400 `invalid_request` (support #214, #219)

With a valid token, the URL from `auth_init` opens Intervals' authorize page
and gets `{"error":"invalid_request"}` before the consent screen. Changing
`state` or `redirect_uri` gave the same body, so the request is rejected
before those are checked.

What I checked:
- The scope syntax (`ACTIVITY:READ,...,CALENDAR:WRITE`, comma-separated, no
  spaces) matches Intervals' documented format, so the scope string itself is
  not malformed.
- The breakage started with the calendar sync on 2026-10-02, which added
  `CALENDAR:*` scopes. Scope validation against the registered app is the
  likely reason, but I could not confirm it against the live server.

**Most likely cause:** `config.py` hard-coded the dev placeholder client
(`tricoach-dev` / `s3cr3t-placeholder-0000`), even though the README says the
real pair is in the deploy environment. Intervals does not know that client
for the production app, so the request is rejected.

**Fix:** `config.py` reads `INTERVALS_CLIENT_ID` and `INTERVALS_CLIENT_SECRET`
from the environment and keeps the placeholders only as local-dev defaults.

**Not yet done (needs you):** set those two variables in the deploy environment
and check that the registered Intervals app has the `CALENDAR` scopes enabled.
If the 400 persists with the real client, the next thing to check is that
registration, not the code. I did not deploy or contact Intervals.

## 3. Rivera's connection "expired" an hour after onboarding (support #219)

The token response had no `expires_in` and no `refresh_token`
(`connect-attempt.log`, 2026-09-19). The server defaulted `expires_in` to
3600 s, then the refresher found no refresh token and marked the connection
`expired, reconnect` at 18:37, about an hour after connecting. The token itself
had no stated lifetime.

**Fix:** a missing `expires_in` now means "no stated expiry", not one hour.
The refresher skips such connections. A connection that does expire without a
refresh token is still marked expired.

## Other changes

- `refresh_tokens` no longer holds `LOCK` during the network call to Intervals.
  Previously one slow refresh blocked every request handler for up to 15 s per
  connection.
- A refresh that finishes after the user has disconnected or reconnected can
  still overwrite the newer connection. I did not fix that; it needs a
  compare-and-set on the refresh token.

## What was tested

- `python3 -m py_compile` on `server.py` and `config.py`.
- Running the server locally: `auth/init` with a Bearer token returns the
  authorize URL as JSON; without one it returns 401. `status` returns
  disconnected.
- In-process: a token with no `expires_in` stores `expires_at = None`; a token
  with `expires_in` keeps the expected expiry.
- Not tested: the real Intervals authorize, callback, and refresh, because
  they need the deploy client credentials and network access to Intervals.
