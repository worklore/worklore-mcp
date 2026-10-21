# Intervals.icu connection: causes and fixes

## 1. Connect button returns 401 for everyone (ticket #214)

The button was a plain link, `<a href="/api/intervals/auth/init">`, and
`auth_init` sits behind `require_user()`. Following a link is a normal page
navigation, and the browser doesn't attach the SPA's `Authorization: Bearer`
header to it, because that token lives in `localStorage` and only goes out on
`fetch`. So every click reached the server with no header, and the user got
`{"error": "unauthorized"}`. This matches `logs/connect-attempt.log` §1: a
document GET with no Authorization header.

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that
returns `{"authorize_url": ...}` as JSON. The button calls it through the
`api()` fetch wrapper, then calls `window.location.assign(authorize_url)`. The
old GET route is gone.

## 2. Authorize step rejected with `invalid_request` (the pasted-link workaround, since 2026-10-02)

`config.SCOPES` was
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu allows each scope area only once, and `:WRITE` already includes
`:READ`. Asking for both READ and WRITE on the same area is rejected
("Duplicate scope"). Here both ACTIVITY and CALENDAR were duplicated. Calendar
sync added `CALENDAR:READ,CALENDAR:WRITE`, which matches the ticket's timing.
Rivera's grant on 2026-09-19 has the shape a valid request produces:
`ACTIVITY:WRITE,WELLNESS:READ`, one entry per area.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

Caveat: the captured 400 only says `invalid_request` and doesn't name the
parameter that failed. The scope is the one thing that changed and the one
thing that breaks a documented Intervals rule. Still, this cause is inferred,
not confirmed against the live service (I made no external calls).

## 3. A working connection marked "expired, reconnect" after about an hour (ticket #219)

Intervals.icu tokens have no `expires_in` and no `refresh_token`. They stay
valid until the athlete revokes the app. The old code treated the missing
`expires_in` as `DEFAULT_TOKEN_TTL = 3600`, and a background "refresher"
thread found no refresh token when that hour ran out. It then wiped the
access token and set `status = "expired, reconnect"`. That's exactly what the
log shows for Rivera (17:41 connected, 18:37 expired), even though Rivera had
revoked nothing. The token was still valid; our own server threw it away.

**Fix:** removed the TTL, `expires_at`, `refresh_token` and the refresher
thread. Revocation is now detected lazily: a 401 from the Intervals API
clears the stored token and sets the status to `revoked, reconnect`. The SPA
then shows the reconnect prompt instead of failing.

## Other changes made while in there (not causes of the reported failures)

- **Token exchange** now sends only `client_id`, `client_secret` and `code`,
  which is what Intervals expects. The extra `grant_type`/`redirect_uri`
  fields were evidently tolerated, since Rivera's exchange worked.
- **`state`** is now a signed HS256 JWT with `sub` (the user id),
  `purpose: "intervals_oauth"`, a 15-minute `exp` and a nonce. The callback
  checks the signature, purpose and expiry before exchanging the code. It
  replaces the ad-hoc `user:ts:truncated-hmac` string.
- **Account-mismatch guard:** a reconnect callback that comes back with a
  different athlete id than the one already linked is rejected with a 409.
  The athlete has to disconnect first.
- The token response must include `access_token` and `athlete.id`, or the
  callback fails cleanly.

## Verified / not verified

- Verified locally against a mock Intervals server (`INTERVALS_BASE`
  override), with nothing sent to intervals.icu:
  - GET on init → 404; POST → JSON authorize URL with the deduplicated scope.
  - Callback → 302, and the token POST carries only the three fields.
  - A tampered state → 400.
  - Status and wellness work.
  - A different athlete on reconnect → 409.
  - A 401 from Intervals → token cleared, status `revoked, reconnect`.
- Not done (needs a real account and the real client pair from the deploy
  env), per the guide:
  - Complete the flow on intervals.icu and confirm `/wellness` returns data.
  - Revoke the app in Intervals settings and confirm the app falls back to
    "reconnect".
  - Confirm a duplicated-area scope is rejected.
- Still open: **encrypt the access token at rest** in the prod Postgres
  table. It's a non-expiring credential. The dev server keeps it in memory,
  and stdlib has no cipher, so this belongs in the prod storage layer.
- Rivera's connection was cleared by our bug, not revoked, so Rivera has to
  reconnect once (the button works now). The new scope adds `CALENDAR:WRITE`,
  which Rivera's old grant didn't include, so Intervals will probably show the
  consent screen again.
