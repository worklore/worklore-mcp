# Intervals.icu connection: causes and fixes

## Causes

### 1. The Connect button is a GET link, so it always 401s
`static/app.js` rendered `<a href="/api/intervals/auth/init">`. A full-page
navigation does not send the `Authorization` header that the SPA keeps in
`localStorage` (headers only travel on fetch/XHR). `require_user()` then
returned 401 for everyone. Log entry 1 in `logs/connect-attempt.log` shows
exactly this request (`GET /api/intervals/auth/init 401 (no Authorization header)`).
This is why nobody gets past the button (ticket #214).

**Fix:** `auth_init` is now `POST` and returns `{"authorize_url": ...}` as JSON.
The button calls it through the authenticated fetch wrapper and then runs
`window.location.assign(authorize_url)`.

### 2. The scope string repeats areas, so Intervals rejects the authorize request
`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Both `ACTIVITY` and `CALENDAR` appear twice. `:WRITE` already implies `:READ`.
Log entry 2 shows the hand-built authorize URL answered with HTTP 400
`{"error":"invalid_request"}`, and no consent screen appeared. The calendar
scopes were added on 2026-10-02, which is why pasting the link stopped
working then (ticket #219).

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Each area
appears once. Caveat: the Intervals 400 body in our logs does not name the
parameter, so the duplicate scope is the cause that fits. I did not confirm
it against the live service (see "Not verified").

### 3. The token is given a one-hour lifetime it doesn't have
Intervals returns no `expires_in` and no `refresh_token`. `store_connection`
fell back to `DEFAULT_TOKEN_TTL = 3600`, so the connection was marked expired
an hour after it was made. The refresher then found no refresh token and set
`status = "expired, reconnect"`. Log entries 3 show this for T. Rivera:
connected at 17:41, expired at 18:37, and Rivera had not revoked anything on
the Intervals side (ticket #219). The access token was still valid.

**Fix:** the expiry assumption and the refresher thread are gone. A connection
stays `connected` until Intervals rejects the token. `wellness()` now handles
that lazily: on a 401 from Intervals it clears the access token, sets
`status = "expired, reconnect"`, and returns 409. The UI then shows the
reconnect state instead of failing.

## Changes

- `config.py`: scope string corrected; `REFRESH_INTERVAL` removed.
- `server.py`: init is `POST` returning JSON; the GET route is removed;
  `store_connection` no longer assumes an expiry; the refresher thread is removed;
  a 401 from Intervals clears the token and marks the connection for reconnect.
- `static/app.js`: the link becomes a button that POSTs for the authorize URL and navigates to it.

## Colleague's note: what applied

- **Rule 1 (no refresh_token, token lives until revoked, handle 401 lazily): applied.**
  This matches our own Rivera log. Dropped the refresh machinery.
  *Not applied:* "encrypt at rest". Tokens live in memory in this dev server.
  Encryption belongs with the Postgres table in prod, which I can't see here.
- **Rule 2 (each area once, WRITE implies READ): applied.** I used
  `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. The colleague also had
  `SETTINGS:WRITE`. Not added, because this app doesn't call settings.
  The note's `Duplicate scope` wording is not in our logs. Our logs only show `invalid_request`.
- **Rule 3 (token exchange, athlete id in the response): partly applied.** The
  athlete id from the token response is used directly (no "who am I" call).
  *Not applied:* dropping `grant_type` and `redirect_uri`. Our own log shows
  the 2026-09-19 exchange succeeded with them present, so they are accepted.
  Removing them is not needed for the fix.
- **Rule 4 (init must be an authenticated POST, not a GET link): applied.**
  This is the exact cause of the 401 in log entry 1.
- **State as a JWT with a `purpose` claim, plus an account-mismatch guard on reconnect: not applied.**
  The state is already HMAC-signed with a 15-minute max age, so it is not one of the causes.
  The `purpose` claim and the mismatch guard would be worthwhile hardening, but I left them out of this fix.

## Not verified / open

- **No live Intervals run.** I could not reach a real Intervals.icu account
  here, and the placeholder client is not registered. I tested the full
  server flow against a local stub that mimics the note's behaviour (no
  refresh_token, no expires_in, `Duplicate scope` on repeated areas). Results:
  - Old scope string rejected by the stub; new scope accepted.
  - POST init returns `authorize_url`; GET init is 404; POST without auth is 401.
  - Callback exchanges the code, stores the connection, and redirects to `/?connected=1`.
  - Wellness returns 200 with the token.
  - After the stub revokes the token, wellness returns 409 and status becomes `expired, reconnect`.
  The stub is not Intervals itself, so the live check is still needed.
- **Redirect URI.** `http://localhost:8766/api/intervals/callback` must be
  registered on the Intervals OAuth client. I have no way to confirm that from the repo.
- **Running server is stale.** A `server.py` started before my edits is
  listening on `127.0.0.1:8766` (PID 94527). It is still running the old code,
  so restart it before testing. I did not stop it, since it isn't mine.
- **Dev sign-in default.** `static/app.js` falls back to `tok-okafor` when
  `localStorage` has no token. That's fine for dev but should not ship.
