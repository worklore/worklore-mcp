# Intervals.icu connection: causes and fixes

Three separate bugs. Any one of them would be enough to break the integration.

## 1. The Connect button always 401s (ticket #214, log §1)

The button was a plain link, `<a href="/api/intervals/auth/init">`. When the
browser follows a link it loads a new page, and that request does not include
the `Authorization: Bearer` header. Only the SPA's `fetch` wrapper adds that
header (the token lives in `localStorage`). So `require_user()` always
rejected the request. The dev-tools capture in the log confirms the request
had no Authorization header.

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that
returns `{"authorize_url": ...}` as JSON. The button calls it through `api()`
and then runs `window.location.assign(authorize_url)`. The callback still
gets the user from the signed `state`, since Intervals' redirect back to us
has no auth header either.

## 2. The authorize step returns `400 invalid_request` (ticket #219, log §2)

On 2026-10-02 the calendar sync shipped and the scope became
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
That names ACTIVITY twice and CALENDAR twice. In Intervals, `:WRITE` already
includes `:READ`, and a repeated area is rejected as a duplicate scope. Here
the rejection showed up as a bare `{"error":"invalid_request"}`, which is why
changing `state` or `redirect_uri` made no difference. The scope Intervals
granted to Rivera on 09-19 was `ACTIVITY:WRITE,WELLNESS:READ`, one entry per
area, which fits this explanation.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. A working connection is marked "expired, reconnect" after an hour (ticket #219, log §3)

Intervals tokens have no `expires_in` and there is no `refresh_token`. They
stay valid until the athlete revokes the app. `store_connection()` filled in
a made-up `DEFAULT_TOKEN_TTL = 3600` anyway. The background refresher then saw
"expiry passed, no refresh token", threw the valid token away and set
`expired, reconnect`. That matches the log: connected at 17:41, expired at
18:37, while Rivera had revoked nothing.

**Fix:** removed the fake TTL, the `expires_at`/`refresh_token` fields, the
refresher thread and `REFRESH_INTERVAL`. Revocation is now detected when it
actually happens: if Intervals returns 401 on an API call, the connection's
token is cleared, its status becomes `revoked, reconnect`, and the endpoint
returns 409 "not connected" (the same response the UI already handles).

Rivera's stored token was already wiped by the refresher, so Rivera has to
click Connect once more. After that the connection will last.

## Verification

Tested locally against a stub Intervals server (`INTERVALS_BASE` override):
- `GET /api/intervals/auth/init` → 404 (no longer a GET route)
- `POST` without a token → 401
- `POST` with a token → JSON `authorize_url` with the corrected scope
- callback → 302, status connected, wellness 200
- after a simulated revoke: wellness → 409, status `revoked, reconnect`

`app.js` was syntax-checked. I did not test against real Intervals.icu (I had
no credentials and stayed inside this repo).

## Colleague's note: what applied

- **Applied, §4 (init must be POST, frontend uses `location.assign`):** this
  is cause 1 exactly, and I used the same fix.
- **Applied, §2 (Duplicate scope):** cause 2. Our error text was
  `invalid_request` rather than `Duplicate scope`, but it is the same problem.
  I did **not** copy the note's scope string. Its `SETTINGS:WRITE` is
  something this app doesn't need; I kept our own areas, one entry each.
- **Applied, §1 (no refresh, no expiry; handle 401 lazily):** cause 3, fixed
  as the note suggests.
- **Checked, not needed, §3 (token exchange takes only `client_id`,
  `client_secret`, `code`):** our exchange also sends `grant_type` and
  `redirect_uri`, and it worked for Rivera on 09-19. It isn't a cause, so I
  left it unchanged.
- **Not applied:** a JWT `state` with a `purpose` claim (our HMAC state
  already carries the user id with a 15-minute TTL and is checked before the
  exchange); an account-mismatch guard on reconnect; encrypting tokens at
  rest (prod storage isn't in this repo, though since tokens never expire
  this is worth doing in prod). The note's forum and registration steps
  didn't apply either.
