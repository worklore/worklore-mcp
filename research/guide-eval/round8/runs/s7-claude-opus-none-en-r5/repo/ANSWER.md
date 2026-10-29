# Intervals.icu connection: causes and fixes

Three separate bugs. Each one alone was enough to block athletes.

## 1. The Connect button never sends the sign-in token (ticket #214, log §1)

The SPA keeps the tricoach token in `localStorage` and only sends it as an
`Authorization: Bearer` header from its `fetch` wrapper. "Connect Intervals.icu"
was a plain `<a href="/api/intervals/auth/init">`, so clicking it caused a
top-level browser navigation. Browsers don't attach custom headers to a
navigation, and the token is not in a cookie. `require_user()` therefore got
no header and returned `401 {"error":"unauthorized"}` for every athlete.
The log shows exactly this: `401 (no Authorization header)`, with
`Accept: text/html` and a document navigation.

**Fix:** the button now calls `POST /api/intervals/auth/init` through the `api()`
wrapper, so the header is sent. The server returns `{"url": <authorize URL>}`
and the SPA does `location.assign(url)`. `GET` still answers with a 302 for
clients that send the header themselves (curl, scripts). (`static/app.js`,
`server.py: auth_init`)

## 2. The scope list makes Intervals reject the authorize request (log §2)

When calendar sync shipped on 2026-10-02, `SCOPES` became
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals expects each area once, with either `:READ` or `:WRITE`, and
`WRITE` already includes read. Rivera's grant from before that change shows
this: it came back as `ACTIVITY:WRITE,WELLNESS:READ`, with no separate
`ACTIVITY:READ`. Listing the same area twice gets
`400 invalid_request` before the consent screen. Removing `state` or changing
`redirect_uri` gave the same error, which points at the scope rather than
those parameters.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`, which is the
same access as before (`config.py`).

## 3. Working connections were expired by our own code after an hour (ticket #219, log §3)

Intervals.icu OAuth access tokens don't expire. The token response has no
`expires_in` and no `refresh_token` (see Rivera's response in the log), and the
token stays valid until the athlete revokes the app. `store_connection()`
filled in a made-up `DEFAULT_TOKEN_TTL = 3600` when `expires_in` was missing.
About 55 minutes later, the refresher saw "expiring and no refresh token" and
set the connection to `expired, reconnect` and deleted the access token.
Intervals never revoked anything; Rivera still had tricoach listed as an
authorised app.

**Fix:** if the provider sends no `expires_in`, the connection has no expiry
(`expires_at = None`) and the refresher skips it. The refresh path still works
if a provider does send expiries. A connection is now marked
`expired, reconnect` only when Intervals actually rejects the token (a 401
from the wellness proxy) (`server.py`).

## Verified

I tested locally against a stub Intervals token endpoint (nothing external
was contacted):

- an unauthenticated GET still gets 401
- the POST with the header returns the authorize URL with the new scope
- the callback stores the connection as a "non-expiring token"
- after several refresher passes, the status is still `connected`

I could not test against the real intervals.icu. The scope cause is inferred
from the logs and Intervals' documented scope format.

## Follow-up for affected athletes

Rivera's stored connection was already wiped (the access token was set to
`None`), so they need to click Connect once more after this ships. Their
Intervals grant is still there, so they won't need to set anything up again
on the Intervals side.

Not changed, but worth noting: `APP_SECRET` and the client secret in
`config.py` are dev placeholders. Make sure prod overrides them.
