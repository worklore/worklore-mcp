# Intervals.icu connection: causes and fixes

There are three separate bugs. Each one would stop athletes from connecting on its own.

## 1. The Connect button can never authenticate (everyone gets `{"error": "unauthorized"}`)

The SPA signs in with a token stored in `localStorage`. That token only reaches the
server as `Authorization: Bearer …`, which the `api()` fetch wrapper adds. The Connect
button was a plain `<a href="/api/intervals/auth/init">`, so clicking it was an ordinary
page navigation. Browsers never add an `Authorization` header to a navigation, so
`require_user()` saw no token and returned 401 every time. The 401 in
`logs/connect-attempt.log` §1 shows this: it is a document navigation with no auth
header. Rivera only got through by having a link built by hand.

**Fix:** `/api/intervals/auth/init` is now a `POST` endpoint that returns
`{"url": …}`. The button calls it through `api()`, so the Bearer token is sent, and then
sets `window.location` to the returned Intervals authorize URL (`static/app.js`,
`server.py`). The endpoint returns the URL instead of a 302 because `fetch` would follow
a cross-origin redirect and fail on CORS. The signed `state` still carries the user
through the redirect.

## 2. The authorize step rejects the requested scopes (400 `invalid_request`, no consent screen)

On 2026-10-02 the calendar sync changed `SCOPES` to
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. Intervals.icu
expects one entry per area, either `AREA:READ` or `AREA:WRITE`, and `WRITE` already
includes read. Rivera's token from before that change shows the format Intervals uses:
`"scope":"ACTIVITY:WRITE,WELLNESS:READ"`. Asking for both READ and WRITE on the same area
is a malformed request, so `/oauth/authorize` returns `invalid_request` before the
athlete sees the consent screen. This also explains §2 of the log: removing `state` or
changing `redirect_uri` returned the same error, because neither was the problem.

**Fix:** `config.SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. This keeps the
same access: activities read/write, wellness read, calendar read/write.

*Caveat:* the ground rules don't allow calls to intervals.icu, so I couldn't test this
against the real server. The conclusion comes from the logs, Rivera's granted scope and
the timing of the 2026-10-02 change. If the 400 continues, the next thing to check is
whether the OAuth client registered with Intervals allows the CALENDAR scope and the
exact `redirect_uri`.

## 3. Working connections were marked "expired, reconnect" after an hour (Rivera)

Intervals.icu access tokens don't expire. The token response has no `expires_in` and no
`refresh_token`, as Rivera's logged response shows. `store_connection()` filled in a
made-up `DEFAULT_TOKEN_TTL = 3600`. When that passed, the refresher found no refresh token
and wiped a valid token, setting the status to "expired, reconnect". That matches the log
line about 56 minutes after connecting (the refresher acts 5 minutes early).
Intervals never revoked anything, and the app is still listed under Rivera's Intervals
apps.

**Fix:** if the provider sends no `expires_in`, `expires_at` is now `None` and the
refresher leaves the connection alone. A connection is only marked expired when an
expiry actually given by the provider has passed, or when Intervals rejects the token
(a 401 from the wellness proxy, meaning the athlete revoked access). Refresh-token
handling is kept for any response that does include an expiry.

## Smaller changes

- The callback now handles `?error=…` (for example when the athlete clicks Deny on the
  consent screen) by redirecting back to the app, where before it showed "bad state or
  code".
- The connect log line now records the granted scope.

## Verification

I ran the patched server against a local mock of the Intervals token and API endpoints:

- An unauthenticated GET to the old link now returns 404, and the authenticated `POST`
  returns the authorize URL with the new scopes.
- The callback exchanges the code and stores the connection with no expiry.
- `/status` reports connected and `/wellness` is proxied.
- `?error=access_denied` redirects back to the app.

Rivera has to connect once more, because the old token was cleared in memory. After that,
the connection should not expire.
