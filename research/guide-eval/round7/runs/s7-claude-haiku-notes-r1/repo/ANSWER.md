# Intervals.icu connection: causes and fixes

Athletes could not connect, and the one connection that worked expired after
about an hour. There were four causes. Three are fixed in code; the
fourth (encryption at rest) is out of scope here.

## 1. The Connect button sent a GET with no `Authorization` header

`static/app.js` rendered `<a href="/api/intervals/auth/init">`, and
`server.py` only accepted that path as GET. A link navigation does not send
the `Authorization` header the SPA keeps for `fetch` calls, so every athlete
got `{"error": "unauthorized"}` (logs/connect-attempt.log, section 1; support
#214).

**Fix:** `auth/init` is now an authenticated `POST` that returns
`{"authorize_url": ...}`. The button calls it with the usual fetch wrapper,
then does `window.location.assign(authorize_url)`. The GET route is removed.

## 2. Duplicate scope areas made Intervals reject the authorize step

`config.SCOPES` listed `ACTIVITY:READ,ACTIVITY:WRITE` and
`CALENDAR:READ,CALENDAR:WRITE`. `:WRITE` covers `:READ` for the same area,
so each pair is a duplicate. Since the calendar sync shipped on 2026-10-02,
Intervals answers the authorize step with `400 {"error":"invalid_request"}`
before the consent screen (logs/connect-attempt.log, section 2; support #219).
The body does not name the bad parameter. Removing `state` or changing
`redirect_uri` gave the same body, so the scope is the likely culprit. I could
not hit the live authorize endpoint to confirm this.

The 2026-09-19 connection is consistent with this. It was granted
`ACTIVITY:WRITE,WELLNESS:READ` even though the app had requested
`ACTIVITY:READ` too, so Intervals normalizes `:READ` into `:WRITE`.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Each area
appears once. The app reads wellness and writes activities and calendar
entries, and nothing reads calendar or activity data without writing it.

## 3. The app invented a one-hour token expiry

Intervals' token response has no `expires_in` and no `refresh_token`
(logs/connect-attempt.log, section 3). `store_connection` fell back to
`DEFAULT_TOKEN_TTL = 3600`, so the connection was marked expired an hour
after it was made. The refresher then set `status = "expired, reconnect"`.
The athlete was told to reconnect, and Connect failed for the reason in
cause 1 (support #219).

**Fix:**
- No `expires_in` means `expires_at = None`: no expiry is invented. The
  refresher skips connections with no expiry, and a refreshed token without
  `expires_in` also gets no expiry.
- The API is the source of truth for revocation. A 401 from
  `/api/v1/athlete/{id}/wellness` now drops the access token and sets
  `expired, reconnect`, and the endpoint returns 409 so the SPA can prompt a
  reconnect. Previously the connection stayed "connected" and the athlete saw
  a raw 401.

## 4. Not changed: tokens are held in memory, unencrypted

The reference note (`notes/intervals-icu-oauth-quirks-no-refresh-token-duplicate-scope.md`)
says to encrypt stored tokens at rest. The current code keeps them in a
plain in-memory dict, which matches the stated dev setup. Encryption belongs
with the Postgres move and is not part of this fix.

## Notes on the reference note

The note's claims about the token exchange (only `client_id`, `client_secret`,
`code`) and the "Duplicate scope" error text are not verified here. The
exchange code still sends `grant_type` and `redirect_uri`, which worked for
Rivera on 2026-09-19. I left it unchanged.

## Verification

I ran `server.py` against a local mock of Intervals (not the real service,
and nothing was sent to it). The mock returned the same token shape Rivera
got. All checks passed:

- `GET /api/intervals/auth/init` returns 404; `POST` with a bearer token
  returns `authorize_url` with the new scope string (no duplicate areas) and
  a signed `state`.
- `POST` without an `Authorization` header returns 401.
- The callback stores the connection with no expiry and no refresher expiry
  pass.
- Wellness returns 200 while the token is valid. After the mock revokes it,
  wellness returns 409, `status` reports `expired, reconnect`, and a new
  `POST` init still works.
- `static/app.js` passes `node --check`, and `server.py`/`config.py` compile.

Not verified: the live authorize step with the new scope. The real client
must be re-registered or checked against Intervals before the next athlete
connects.
