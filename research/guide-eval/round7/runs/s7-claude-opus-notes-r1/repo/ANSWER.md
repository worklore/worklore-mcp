# Why athletes can't connect Intervals.icu

Three separate bugs. Fixing just one of them still leaves the integration broken.

## 1. The Connect button never sends the sign-in token (everyone gets 401)

`static/app.js` rendered Connect as a plain link, `<a href="/api/intervals/auth/init">`.
The sign-in token lives in `localStorage` and only reaches the server through the
`api()` fetch wrapper. When the browser follows a link it doesn't add the
`Authorization` header, so `auth_init` → `require_user()` returned
`{"error": "unauthorized"}` for every athlete. You can see this in
`connect-attempt.log` §1: the request is a document navigation and the server logs
"no Authorization header".

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that returns
`{"authorize_url": ...}` as JSON. The Connect button calls it through `api()` and
then runs `window.location.assign(authorize_url)`. The GET route is gone.
The callback still identifies the user by the HMAC-signed `state` (15-minute
TTL), because Intervals' redirect back to us has no auth header either.

## 2. The scope list names areas twice (Intervals answers 400 `invalid_request`)

`config.SCOPES` was
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
On Intervals, `:WRITE` already includes `:READ`, and a scope list that names the
same area twice is rejected ("Duplicate scope") before the consent screen
appears. That explains why pasting the authorize link stopped working once the
calendar sync added `CALENDAR:READ,CALENDAR:WRITE` (§2 of the log). Rivera's
grant on 2026-09-19 came back as `ACTIVITY:WRITE,WELLNESS:READ`, which is the
form Intervals expects.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Each area
appears once, with the highest access level needed.

## 3. Working connections get thrown away after an hour ("expired, reconnect")

Intervals access tokens have no `expires_in` and no `refresh_token`. They stay
valid until the athlete revokes the app. `store_connection` filled in a made-up
`DEFAULT_TOKEN_TTL = 3600`, so `expires_at` was set to one hour out. The
refresher then saw an "expiring" token with no refresh token, wiped the
`access_token`, and set the status to `expired, reconnect`. That is exactly what
Rivera hit (§3 of the log, 17:41 connect → 18:37 expired). Intervals had not
revoked anything, and tricoach is still listed under their Intervals apps.

**Fix:** if the token response has no `expires_in`, `expires_at` is `None` and
the refresher skips that connection. It still refreshes tokens that do carry
an expiry. Revocation is now detected when it happens: a 401 from the
Intervals API (in `/api/intervals/wellness`) marks the connection
`expired, reconnect`.

## Notes / follow-ups

- Rivera's stored access token was already deleted by the old code, so
  Rivera has to click Connect once more. After that the connection should last.
- Not changed: the token exchange still sends `grant_type` and `redirect_uri`.
  Rivera's exchange succeeded with them, so they aren't causing the failure.
- Worth adding later: an account-mismatch guard on reconnect (reject a callback
  whose athlete id differs from the stored one), and encrypting tokens at rest
  in prod, since they never expire.
- Verified locally against a stub Intervals server: the full flow works
  (init → authorize → callback → status → wellness) and the stub accepts the
  new scope list. A token without `expires_in` survives refresher passes. A
  duplicated scope list gets a 400, which matches what the real service returned.
  I could not test against real intervals.icu from here.
