# Intervals.icu connection: causes and fixes

There are three separate defects. Each one alone is enough to break the connection.

## 1. The Connect button can never authenticate (ticket #214, log §1)

The button was a plain link, `<a href="/api/intervals/auth/init">`. Clicking it
navigates the whole page, and a page navigation does not send the
`Authorization: Bearer` header. That header only comes from the SPA's `fetch`
wrapper, which reads the token from `localStorage`. So `require_user()`
returned 401 to every athlete: `GET /api/intervals/auth/init 401 (no
Authorization header)`, and the browser showed a white page with
`{"error": "unauthorized"}`.

**Fix:** `POST /api/intervals/auth/init` is now called through the
authenticated `api()` wrapper and returns `{"authorize_url": ...}` as JSON.
The SPA then calls `window.location.assign(authorize_url)`. The old GET route
is gone and now returns 404. The callback stays an unauthenticated GET, and
the user is still identified by the HMAC-signed, 15-minute `state` parameter
that already existed. (`server.py` `auth_init`/`do_POST`, `static/app.js`)

## 2. The authorize URL is rejected because of duplicate scopes (ticket #219, log §2)

`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu allows each area only once, and `:WRITE` already includes
`:READ`. Listing both for ACTIVITY and CALENDAR makes Intervals answer
`400 {"error":"invalid_request"}` before the consent screen appears. This
started with the calendar-sync release on 2026-10-02, which is also when
pasting the link by hand stopped working. Rivera's earlier grant shows only
`ACTIVITY:WRITE,WELLNESS:READ`, which is consistent with this.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. Working connections were expired after an hour (ticket #219, log §3)

Intervals.icu tokens have no `expires_in` and no `refresh_token`. They stay
valid until the athlete revokes the app. `store_connection()` filled in a
made-up `DEFAULT_TOKEN_TTL = 3600`, and then the background `refresh_tokens()`
thread found no refresh token and marked the connection
`expired, reconnect`, throwing away a token that still worked. That is why
Rivera's connection died about an hour later even though they had revoked
nothing.

**Fix:** I removed the fake TTL, the `refresh_token` and `expires_at` fields,
the refresher thread, and `REFRESH_INTERVAL`. Revocation is now detected when
it happens: a 401 from the Intervals API clears the token, sets the status to
`revoked, reconnect`, and returns 409 to the SPA, which then shows the Connect
button again.

## How it was checked

I ran `server.py` with `INTERVALS_BASE` pointing at a local fake Intervals
server. The fake rejects a repeated scope area with `invalid_request` and
issues a token with no expiry. In that setup:

- GET init returns 404.
- POST init without a token returns 401.
- POST init with a token returns `authorize_url` with the new scopes.
- The authorize step, the callback and the token exchange succeed, and
  `/status` shows the connection.
- Wellness returns data.
- After revoking on the fake side, wellness returns 409 and the status is
  `revoked, reconnect`.

This has not been run against the real intervals.icu. That still needs a real
client and account, as the note's "Verify" section describes.

## Which parts of the colleague's note applied

- **Applied:**
  - **#4 (init must be an authenticated POST returning `{authorize_url}`)**
    is exactly cause 1.
  - **#2 ("Duplicate scope")** is cause 2. Our error body only says
    `invalid_request`, but the doubled scopes in the URL match the note. I
    used our own scope set and did not copy the note's (we don't need
    `SETTINGS:WRITE`).
  - **#1 (no refresh_token or expiry; handle revocation on the first 401)**
    is cause 3.
- **Already in place:** a signed `state` carrying the user id with a 15-minute
  TTL. Ours is an HMAC token rather than a JWT with a `purpose` claim. That
  difference doesn't matter here, so I left it alone.
- **Not applied:**
  - **#3 (token exchange takes only `client_id`/`client_secret`/`code`):**
    our exchange also sends `grant_type` and `redirect_uri`, and Rivera's
    exchange succeeded with them. They weren't causing any failure, so I left
    the exchange unchanged.
  - **Not done, possible follow-ups:** encrypting tokens at rest (this dev
    server keeps everything in memory) and the account-mismatch guard on
    reconnect. Neither is behind the reported failures.
- **Ignored:** the forum link and client-registration steps. Nothing was sent
  to any external service.
