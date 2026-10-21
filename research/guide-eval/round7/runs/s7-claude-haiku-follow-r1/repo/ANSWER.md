# Intervals.icu connection: causes and fixes

Connect failed for every athlete, and the one connection that worked (T. Rivera,
2026-09-19) was marked "expired, reconnect" about an hour later. Four separate
causes, all in the code and config in this repo.

## Causes

### 1. Connect was a GET link, so it never carried the sign-in token (every athlete)

`static/app.js` rendered `<a href="/api/intervals/auth/init">`. A link is a
full-page navigation, and navigations don't send the `Authorization` header that
the SPA's fetch wrapper adds. `server.py` answered 401 every time
(`logs/connect-attempt.log`, section 1). Support ticket #214 is this.

Fix: init is an authenticated `POST /api/intervals/auth/init`. It returns
`{authorize_url}` as JSON, and the button calls `api(...)` (which sends the
header) and then `window.location.assign(authorize_url)`.

### 2. The authorize step rejects duplicate scope areas (every athlete, and why the paste workaround died)

`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
That lists ACTIVITY and CALENDAR twice. `:WRITE` already implies `:READ`, so
Intervals rejects the URL before showing any consent screen (section 2 of the log:
a 400 with no consent screen, for the same URL in a browser and with curl).

The calendar scope was added on 2026-10-02, which is why pasting the link stopped
working then. The `CALENDAR:READ` duplicate was introduced with it.

Fix: `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Each area appears once.
`:READ` is kept only for areas the app never writes (wellness).

### 3. "Reconnect after an hour": a made-up expiry combined with a refresh pass that can't work

Intervals' token response has no `expires_in` and no `refresh_token`
(`logs/connect-attempt.log`, section 3). `store_connection` filled in
`DEFAULT_TOKEN_TTL = 3600`, so the connection looked like it expired after an hour.
The background refresher then saw no refresh token and set the status to
`expired, reconnect`, and it did so without ever contacting Intervals. Rivera had
not revoked anything (ticket #219), so the token was still valid. The app's timer
had simply given up on it.

Fix: no expiry and no refresh machinery. The refresher thread, `REFRESH_INTERVAL`,
`DEFAULT_TOKEN_TTL` and the `refresh_token` field are gone. A token is treated as
valid until Intervals rejects it. On the first 401 from the API, the server drops
the token and sets the status to `reconnect`, and the page shows a reconnect
message. The athlete id is kept so a reconnect is still checked against it.

### 4. The token exchange and the state were not what the provider expects

- The token exchange sent `grant_type` and `redirect_uri`. Intervals' endpoint takes
  only `client_id`, `client_secret` and `code`. Rivera's exchange succeeded with the
  extra fields, so this was not what broke the flow, but it is removed to match the
  provider.
- The `state` was an HMAC string with no `purpose` claim. The callback has no
  authenticated session, so the state is the only way to know which user it belongs
  to. It is now an HS256 JWT with `sub`, `purpose: "intervals_oauth"`, `iat`, and
  `exp` (15 minutes). `verify_state` checks the signature, purpose, and expiry.
- Nothing stopped a reconnect from attaching a different Intervals account to the
  user. The callback now refuses (409) when the incoming athlete id differs from the
  one already stored.

## What changed

- `config.py`: `SCOPES` deduplicated; refresh config removed.
- `server.py`: POST init returning JSON; GET init removed. JWT state with purpose and
  TTL. Token exchange with three fields. No expiry or refresh. 401 from Intervals
  marks the connection `reconnect`. Account-mismatch guard on callback.
- `static/app.js`: Connect is a button that POSTs for the authorize URL and then
  navigates. `reconnect` status shows a reconnect message.
- `test_connect.py` (new): 8 tests against a local fake of Intervals (no network).
  They cover: init is POST-only and needs auth, the authorize URL is accepted and
  scopes are unique, full flow with no expiry, revoked token → reconnect → reconnect
  works, reconnect as a different athlete is refused, and tampered / expired /
  wrong-purpose / missing states are rejected.

Run: `python3 -m unittest -v test_connect` (all 8 pass).

## Not verified and not done

- **Not tested against the real Intervals.icu.** I had no real client credentials and
  did not contact the service. The fake encodes the behaviour in the logs and the
  reproduce notes. The "Duplicate scope" error text in the guide was not seen in our
  logs: they show a generic `{"error":"invalid_request"}` for the duplicated URL. The
  fix is the same either way. The first real check is the authorize URL from a
  real account with the deploy client id.
- **Encryption at rest is not implemented.** The guide asks for encrypted token
  storage. The store is in-memory and has no crypto dependency, so tokens are
  plaintext in memory. This needs doing before the Postgres move.
- **`SETTINGS:WRITE`** from the guide's scope example is omitted, since the app never
  writes settings.
- In-memory state means a server restart drops all connections. Athletes will need to
  connect again after a restart until the database tables are in place.
- Nothing is committed.
