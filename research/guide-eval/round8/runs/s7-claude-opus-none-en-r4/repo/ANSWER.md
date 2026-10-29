# Why athletes can't connect Intervals.icu

Three separate faults. Any one of them is enough to break the connection.

## 1. The Connect button never sends the athlete's sign-in (the 401 everyone gets)

The SPA keeps the tricoach token in `localStorage`, and only `fetch()` calls made
through `api()` attach it as `Authorization: Bearer …`. "Connect Intervals.icu"
was a plain `<a href="/api/intervals/auth/init">`. That makes the browser navigate
to the page directly, so no Authorization header is sent (see
`connect-attempt.log` §1: document navigation, `401 (no Authorization header)`).
`auth_init` calls `require_user()` and responds with `{"error": "unauthorized"}`.
That explains why the athlete still sees "Signed in as C. Okafor" (those calls go
through `fetch`) but hits a white error page. No athlete could ever get through
the button. Support only got around it by building the link with curl.

**Fix:** `/api/intervals/auth/init` is now a `POST` handled by the API. It
authenticates the bearer token and returns `{"authorize_url": …}`. The button
calls it through `api()` and then runs `window.location.assign(authorize_url)`.
A plain `GET` navigation now returns a clear 405 instead of a misleading 401.
While making this change I also tied the `state` to the browser that started the
flow. A random nonce goes into the signed state and into a short-lived HttpOnly
`SameSite=Lax` cookie, and the callback checks that they match. Before this, a
state minted by one account could be completed in another person's browser,
which would link that person's Intervals account to the wrong tricoach user. The
callback now also handles `?error=` coming back from Intervals.

## 2. The scope string is rejected by Intervals (400 `invalid_request`, no consent screen)

The calendar-sync release (2026-10-02) changed `SCOPES` to
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
On Intervals.icu each area takes a single access level, and `WRITE` already
includes `READ`. Asking for both levels of the same area makes the authorize
endpoint fail before it shows consent. The log fits this: removing `state` or
changing `redirect_uri` did not change the error, and the problem started exactly
when the scope list changed. Rivera's earlier successful grant came back as
`ACTIVITY:WRITE,WELLNESS:READ`, which is one level per area.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` in `config.py`.
This still covers reading and writing activities and calendar, and reading wellness.
I checked this against a local fake only, not the real intervals.icu. Please
confirm it with one real connect. If it still returns 400, check that the
deployed OAuth client is allowed to request the `CALENDAR` scope and that its
registered redirect URI matches `REDIRECT_URI`.
The callback now logs any requested scope the athlete did not grant (`NOT
granted: …`), so a partial grant can no longer silently break calendar push.

## 3. Working connections were thrown away after an hour (Rivera's "expired, reconnect")

Intervals.icu OAuth access tokens do not expire. The token response has no
`expires_in` and no `refresh_token` (see Rivera's response in the log), and the
token stays valid until the athlete revokes the app. `store_connection()` assumed
a `DEFAULT_TOKEN_TTL` of 3600 s anyway. About 55 minutes later, the refresher
(which acts 5 minutes before expiry) found no refresh token, marked the connection
`expired, reconnect` and discarded the access token, even though it was still
valid. Rivera never revoked anything. Then, because of fault 1, they could not
reconnect.

**Fix:** the code no longer invents an expiry. When the provider gives no
`expires_in`, `expires_at` is `None` and the refresher skips the connection. The
refresh path still works for tokens that do have an expiry. Because a revoked
grant is now the only way the token stops working, a 401 from Intervals on a data
call marks the connection `revoked, reconnect`.

**Existing data:** in prod, connections already marked `expired, reconnect` had
their `access_token` set to NULL, so those athletes (Rivera at least) have to
click Connect once more. After that the connection stays up.

## Verified

I ran the server against a local fake Intervals token/API server. All of these
behaved as expected: GET navigation gets 405; POST init with a bearer token
returns an authorize URL with the new scopes and sets the nonce cookie; a callback
without the cookie gets 400; a callback with the cookie gets 302 and connects;
status stays `connected` across refresher passes; and wellness is proxied. No
real Intervals.icu endpoint was contacted.
