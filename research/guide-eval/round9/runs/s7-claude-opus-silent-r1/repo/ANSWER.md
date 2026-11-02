# Intervals.icu connection: causes and fixes

There were three separate problems. Each one alone was enough to break the connection.

## 1. The Connect button always returned 401 (ticket #214)

The SPA authenticates with a bearer token from `localStorage`, and only its
`fetch` wrapper (`api()` in `static/app.js`) attaches that token. "Connect
Intervals.icu" was a plain `<a href="/api/intervals/auth/init">`. Following the
link is a normal page navigation, so the browser sent no `Authorization` header
(you can see this in the dev-tools capture in `logs/connect-attempt.log`), and
`auth_init` → `require_user()` returned `{"error": "unauthorized"}`. This
happened to every athlete in every browser, and to Rivera when they tried to
reconnect.

**Fix:** `/api/intervals/auth/init` now returns `{"authorize_url": ...}` as JSON.
The button calls it through `api()`, which sends the token, and then calls
`window.location.assign(authorize_url)`. The callback needed no change because
the signed `state` parameter already identifies the user.

## 2. Intervals rejected the authorize request with 400 `invalid_request` (since 2026-10-02)

The calendar-sync change set the scope to
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu scopes take one access level per area, and `WRITE` already
includes `READ`. Listing an area twice makes the authorize request invalid.
State and redirect_uri were not the cause: the log shows the 400 persists
without them. The working grant from September had `ACTIVITY:WRITE,WELLNESS:READ`,
which is one level per area. Pasting the link by hand stopped working at the
same time for the same reason.

**Fix:** `config.SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. Working connections were marked "expired, reconnect" after about 1 hour (ticket #219)

Intervals.icu OAuth access tokens do not expire. The token response has no
`expires_in` and no `refresh_token` (see Rivera's token response in the log).
`store_connection` still assumed a 3600 s lifetime (`DEFAULT_TOKEN_TTL`). About
5 minutes before that made-up expiry, the refresher found no refresh token,
discarded a valid access token and set the status to "expired, reconnect".
Nothing had been revoked on the Intervals side.

**Fix:** an expiry is scheduled only when the provider sends `expires_in`. If
it doesn't, `expires_at` is `None` and the refresher skips the connection. To
detect a revoked token, the wellness proxy now marks the connection
"expired, reconnect" only when Intervals actually answers 401.

## Notes / follow-ups

- Rivera's stored token was wiped by the bug, and their September grant has no
  calendar scope, so they need to connect once more. Now that the button works
  they can do that themselves. Any other connection made before the scope
  change also has no `CALENDAR:WRITE` and needs a reconnect for calendar sync.
- Verified locally: I stubbed the Intervals token endpoint, then ran init →
  callback → refresher pass. The result was a 200 JSON authorize URL with the
  new scope, a 302 from the callback, and the connection still "connected"
  after the refresher ran. I did not test against the real Intervals.icu.
- **Unrelated but urgent:** `README.md` has a plaintext Intervals client
  secret (the staging command line), and `config.py` has a hard-coded
  fallback secret. Both are committed. Rotate both secrets and load them only
  from the environment. I didn't change these files or contact any service.
