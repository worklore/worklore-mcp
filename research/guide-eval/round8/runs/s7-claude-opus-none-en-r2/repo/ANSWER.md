# Intervals.icu connection: causes and fixes

There are three separate faults. The first one breaks the Connect button for
everyone. The second one breaks the workaround of pasting the authorize link.
The third one disconnects anyone who does get through, about an hour later.

## 1. Connect button → `{"error": "unauthorized"}` (ticket #214)

The tricoach sign-in token lives in `localStorage`. Only the SPA's `fetch`
wrapper sends it, as `Authorization: Bearer …`. But "Connect Intervals.icu"
was a plain `<a href="/api/intervals/auth/init">`. Clicking it navigates the
whole page, and the browser sends no Authorization header on a navigation (no
cookie either, since the app doesn't use one). `auth_init` calls
`require_user()`, which returns 401 for every athlete. `connect-attempt.log` §1
shows this: `401 (no Authorization header)`, and the request is a document
navigation. Rivera only got through because the coach built the link by hand
with curl and a Bearer header.

**Fix:** `/api/intervals/auth/init` now returns `{"authorize_url": …}` as JSON.
The button is now a `<button>`. It fetches that URL through the authenticated
`api()` wrapper and then sends the browser there with
`window.location.assign()` (`static/app.js`, `server.py: auth_init`). The
callback still finds the user from the signed `state`, so it needs no header.

## 2. Authorize step → HTTP 400 `invalid_request` (since calendar sync, 2026-10-02)

When calendar sync shipped, the scope list changed to
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu scopes take one access level per area, either `AREA:READ` or
`AREA:WRITE`, and WRITE already includes READ. Asking for both levels of the
same area is a malformed scope, so Intervals rejects the request before it
shows the consent screen. That is why changing `state` or `redirect_uri`
didn't change the error.

Rivera's working grant from September supports this: the token came back with
`"scope":"ACTIVITY:WRITE,WELLNESS:READ"`, one entry per area. The log also
shows the 400 started when the scope string changed and nothing else did.

**Fix:** `config.SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. This
covers reading and writing activities, reading wellness, and reading and
writing the calendar.

*Caveat:* I worked out the exact rule Intervals applies from the logs and the
returned scope format. I couldn't test it against the live authorize endpoint,
because the ground rules rule out contacting external services. The first real
Connect will confirm it. If Intervals still answers `invalid_request`, check
that the production `redirect_uri` exactly matches the one registered for the
client.

## 3. "Expired, reconnect" about an hour after connecting (ticket #219)

Intervals.icu OAuth access tokens don't expire. The token response has no
`expires_in` and no `refresh_token`, and the token stays valid until the
athlete revokes the app. Rivera's log shows exactly that response. The old
`store_connection` code invented an expiry when the provider gave none
(`DEFAULT_TOKEN_TTL = 3600`). An hour later the refresher found no refresh
token, marked the connection `expired, reconnect` and threw away
`access_token`, even though the token was still valid. Rivera never revoked
anything on the Intervals side. (The refresher also fires 5 minutes before the
invented expiry, which is why the log line comes at 18:37 and not 18:41.)

**Fix:**
- If the response has no `expires_in`, the connection is stored with
  `expires_at = None` (no expiry), and the refresher leaves it alone.
- The refresher now only acts on tokens that really expire and have a refresh
  token. It now makes its network calls outside the global lock. A connection
  is only marked expired when the refresh grant is rejected (400/401). A
  network error or a 5xx is retried on the next pass.
- A connection is marked `expired, reconnect` when Intervals returns 401 on a
  data call (`/wellness`). That is the real signal that the athlete revoked
  access.

## Follow-ups
- Rivera's stored token was set to `None` when the connection was marked
  expired, so it can't be recovered. Rivera has to reconnect once. The button
  works now, and Intervals may skip the consent screen because the app is
  still authorized.
- Any production rows stuck in `expired, reconnect` for the same reason need
  the same one-time reconnect.

## Verification
I ran the server locally against a stub Intervals with
`INTERVALS_BASE=http://127.0.0.1:…`:
- `auth/init` with no header gives 401. With a Bearer token it returns
  `authorize_url` with the new scope.
- The callback gives 302 to `/?connected=1`. The connection is stored with
  "no expiry".
- Several refresher passes, at a 1 s interval, left the connection connected.
- `/wellness` returns data.
