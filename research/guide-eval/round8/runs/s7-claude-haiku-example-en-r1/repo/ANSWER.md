# Intervals.icu connect: causes and fixes

Three separate faults combined. Each one alone breaks the flow for athletes.

## 1. Connect button is a GET link, so it is always 401

`static/app.js` rendered `<a href="/api/intervals/auth/init">`. A top-level
navigation does not send the SPA's `Authorization: Bearer` header (it lives in
`localStorage` and is only attached by the fetch wrapper). `auth_init` requires
a user, so every click returned `{"error": "unauthorized"}`.

Evidence: `logs/connect-attempt.log` section 1 (GET, `Accept: text/html`, no
auth header, 401) and support ticket #214 (every athlete who clicked).

Fix: `auth_init` is now `POST /api/intervals/auth/init` and returns
`{"authorize_url": ...}` as JSON. The button calls it with `fetch` (via the
existing `api()` wrapper, so the header is sent) and then does
`window.location.assign(authorize_url)`. The GET route was removed.

## 2. Scope string names two areas twice

`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Both `ACTIVITY` and `CALENDAR` appear twice. `:WRITE` already implies `:READ`.
Since the calendar sync shipped (2026-10-02) the authorize step returns an
error page before the consent screen, including for a link pasted by hand
(`logs/connect-attempt.log` section 2 and ticket #219).

Fix: `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`: one entry per
area, writes where the app writes (activities, calendar), reads only for
wellness.

Caveat: the captured response body is `{"error":"invalid_request"}`, which
does not name the parameter. The duplicate-area diagnosis comes from the
colleague's note (their `Duplicate scope` error) and fits the config, but I
could not confirm it against the real Intervals.icu. See "Not verified".

## 3. The server invents a one-hour token expiry

`store_connection` defaulted `expires_in` to `DEFAULT_TOKEN_TTL = 3600` when the
token response had none. Intervals' token response has no `expires_in` and no
`refresh_token` (`logs/connect-attempt.log` section 3). The background
refresher then marked the connection `expired, reconnect` one hour after
connecting (`18:37:12`, connected `17:41:04`), with no revocation on the
athlete's side (ticket #219 says tricoach is still listed in their Intervals
apps).

Fix: no expiry is stored, and the refresh thread and `refresh_token` handling
were removed. A connection is dead only when the API returns 401. The wellness
call now clears the token and sets `expired, reconnect` on 401 and returns 409,
and the SPA then shows the Connect button with the status.

## What from the colleague's note applied

- **1 (no refresh_token, token never expires):** applied. Confirmed by the
  token response in the logs. Refresh machinery removed; revocation is handled
  lazily on 401. Encryption at rest was not applied (see below).
- **2 (`Duplicate scope`, one entry per area, `:WRITE` implies `:READ`):**
  applied. Our config had two duplicate areas. Their suggested set also had
  `SETTINGS:WRITE`; I left that out because the app does not use settings.
- **3 (token exchange shape, athlete id in the token response):** partly
  applied. The athlete id is taken from the token response (it already was).
  I did **not** strip `grant_type` and `redirect_uri` from the exchange: the
  logged exchange with those fields succeeded (2026-09-19 17:41:03), so they
  are accepted here.
- **4 (init must be POST, not a link; callback has no auth header):** applied.
  This is cause 1 above. The callback already gets identity from the signed
  `state`, which is the same idea as the colleague's JWT.

Not applied:

- **`state` as a JWT with a `purpose` claim:** the existing HMAC-signed state
  (user id, timestamp, 15-minute check, constant-time compare) already does the
  job. Adding `purpose` would be a small hardening step, not a fix.
- **Account-mismatch guard on reconnect:** would block a legitimate change of
  Intervals account. Not needed to fix the reported failures.
- **Encrypt the stored token at rest:** the store here is in memory. The prod
  store (Postgres, per README) needs a key-management decision that I have not
  made.

## Other things noticed, not changed

- `static/app.js` falls back to `tok-okafor` when `localStorage` has no
  `tc_token`. In the SPA this means any browser without a token is signed in as
  C. Okafor. That is a dev convenience, but it is dangerous in a multi-tenant
  setup. Remove it before deploying.
- `config.py` holds the client secret placeholder and `APP_SECRET`. The real
  values must come from the deploy environment.
- Anyone running the server locally on port 8766 may find that port already in
  use. During testing I found another project's `server.py` listening there.

## Verification

Done against a local stand-in for Intervals.icu (`INTERVALS_BASE` pointed at
`127.0.0.1`, a stdlib mock written for the test and then deleted). The mock
rejected duplicate scope areas, issued tokens without `expires_in` or
`refresh_token`, and returned 401 for revoked tokens.

Baseline (before the fix): `GET /api/intervals/auth/init` without a header
returned 401. The same GET with a Bearer header returned an authorize URL with
the duplicate-area scope, and the mock refused it with `Duplicate scope`.

After the fix:

- `POST /auth/init` without a header: 401. With a Bearer header: 200 with
  `authorize_url`, scope `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
- Authorize redirects to the callback. The callback stores the connection and
  redirects to `/?connected=1`.
- `GET /wellness`: 200. Tampered `state`: 400.
- Revoke at the provider, then `GET /wellness`: 409. Status: `expired, reconnect`.
- Reconnect: callback succeeds and wellness returns 200 again.
- `node --check static/app.js`: passes.

## Not verified

- The real Intervals.icu. I did not call it; I only sent one GET to its
  authorize page by mistake, with a dev client id and state, and got no
  response I could use. The exact error for duplicate scopes is therefore
  unconfirmed, and so is whether `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`
  is accepted. Confirm with a real account before rollout.
- The button in a real browser. I checked the code path and the JS syntax, not
  the page.
- Revocation in the real Intervals UI. The mock stands in for it.
