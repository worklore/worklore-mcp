# Intervals.icu connection: causes and fixes

There are three separate problems. Each one alone is enough to break the connection.

## 1. The Connect button never sends the sign-in token (ticket #214, log §1)

The SPA signs in with a Bearer token from `localStorage`, and only the
`api()` fetch wrapper attaches it. "Connect Intervals.icu" was a plain
`<a href="/api/intervals/auth/init">`, so clicking it was an ordinary page
navigation. A browser navigation does not send an `Authorization` header (the
log shows `Accept: text/html…` and no Authorization). `auth_init` calls
`require_user()`, which answers `401 {"error": "unauthorized"}`. That happens
to every athlete, every time.

**Fix:** `auth_init` now returns `{"url": "<authorize URL>"}` as JSON instead of
a 302. The button calls it through `api()`, so the token is sent, and then does
`window.location.assign(url)`. The signed `state` still ties the callback to
the right user, so the callback itself needs no Bearer header.
(`static/app.js`, `server.py: auth_init`)

## 2. The authorize request is rejected: invalid scope list (ticket #219, log §2)

Intervals.icu scopes are one entry per area, `AREA:READ` or `AREA:WRITE`, and
`WRITE` already includes `READ`. Rivera's successful grant shows this: we asked
for `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ` and got back
`ACTIVITY:WRITE,WELLNESS:READ`. The calendar sync added on 2026-10-02 made the
list `…,CALENDAR:READ,CALENDAR:WRITE`, and from then on the authorize endpoint
returned `400 invalid_request` before showing the consent screen. The log shows
the error body stays the same when `state` or `redirect_uri` change, so the
scope parameter is what it objects to.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` (`config.py`).
This still gives everything the app uses: reading activities and wellness,
plus reading and writing the calendar.

Caveat: this conclusion comes from the logs and the documented scope format. It
was not tested against the real Intervals.icu (the ground rules ruled that out).
If it still returns 400, the next thing to check is that `REDIRECT_URI` exactly
matches the redirect URI registered for the OAuth client in the deploy env.

## 3. Working connections were expired after an hour (ticket #219, log §3)

Intervals.icu access tokens do not expire. The token response has no
`expires_in` and no `refresh_token`, and the token is valid until the athlete
revokes the app. `store_connection` filled the missing `expires_in` with a
made-up `DEFAULT_TOKEN_TTL = 3600`. An hour later the refresher found no
refresh token and marked the connection `expired, reconnect`, discarding a
token that was still valid. That is why Rivera "needed to reconnect" without
revoking anything.

**Fix:** if the provider sends no `expires_in`, `expires_at` is now `None`
(never expires), and the refresher skips those connections. Refresh still
happens for tokens that do come with an expiry. The connection is now marked
`expired, reconnect` only when Intervals actually rejects the token (a 401
from the wellness proxy, meaning the athlete revoked access).

Note: Rivera's existing record already had its access token wiped, so Rivera
has to connect once more. With fixes 1 and 2 the button now works for that.

## Verification

Tested locally against a stub Intervals token endpoint
(`INTERVALS_BASE=http://127.0.0.1:8799`):
- init without a token gives 401
- init with the Bearer token gives JSON with the authorize URL and the new scopes
- the callback exchanges the code and redirects to `/?connected=1`
- status shows the connection, logged as a "non-expiring token"
