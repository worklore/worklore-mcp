# Intervals.icu connection: causes and fixes

Three separate problems, each reproduced in `logs/` or the support tickets.

## 1. "Connect Intervals.icu" always returns `{"error": "unauthorized"}` (ticket #214)

**Cause.** The button was a plain link to `/api/intervals/auth/init`. The
sign-in token lives in `localStorage` and is only added by the SPA's `fetch`
wrapper. A browser navigation does not send that header, so `require_user()`
returns 401 for every athlete. Log section 1 shows exactly this.

**Fix.** `auth_init` now returns `{"url": ...}` as JSON. The button calls
`connect()` in `static/app.js`, which fetches that URL with the bearer token
and then navigates the browser to it.

## 2. Pasting the authorize link returns `400 invalid_request` (ticket #219, log section 2)

Changing `state` or `redirect_uri` gives the same body, so the failing
parameter is one of the others. Two candidates:

**a. Placeholder client credentials are hardcoded (fixed).** `config.py` says
the real `CLIENT_ID`/`CLIENT_SECRET` are "in the deploy env", but the code never
read the environment. Every deploy sent `client_id=tricoach-dev`. Now
`config.py` reads `INTERVALS_CLIENT_ID` and `INTERVALS_CLIENT_SECRET`, and
startup logs a warning if the placeholder id is still in use.
*Not verified:* whether the deploy environment sets these variables. If it
does not, this is the cause of the 400.

**b. Calendar scopes added 2026-10-02 (not fixed in code).** The scope list now
includes `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals may reject a scope the
app registration does not allow. A third-party README for an Intervals OAuth
library lists `CALENDAR:WRITE` and says `CALENDAR` takes `:READ` or `:WRITE`,
but I could not confirm that `CALENDAR:READ` is valid, and that README is not
official docs. The scope list has to be checked against the app registration in
Intervals. I did not contact Intervals.

## 3. "Connected" for about an hour, then "expired, reconnect" (ticket #219)

**Cause.** Rivera's token response (log section 3) had neither `expires_in` nor
`refresh_token`. `store_connection` filled in a made-up 3600-second lifetime
(`DEFAULT_TOKEN_TTL`). The refresher then found no refresh token and marked the
connection expired an hour later. The token was never shown to expire. The
third-party README says Intervals issues no refresh token and no expiry, which
matches what the response showed (unofficial, so treat it as a lead).

**Fix.** When the provider sends no `expires_in`, `expires_at` is `None` and
the connection is not expired locally. A connection is marked expired only when
Intervals rejects its token: the wellness call now turns a 401 into
`expired, reconnect` and a 409 response. The refresher also skips connections
with no expiry, and it no longer holds `LOCK` during network calls.

## Other changes

- `refresh_tokens` no longer holds the global lock during HTTP calls, so a slow
  Intervals response cannot block other requests.
- `logs/connect-attempt.log` contains a partial access token (`9f3c1e0b4d7a...`).
  The server code does not log tokens, so that line came from a debug print that
  is no longer in the code. Redact the file, and consider revoking Rivera's
  token in Intervals.

## Verification

- `python3 -m py_compile` passes for `server.py` and `config.py`.
- The OAuth flow was run locally on port 8800 against a mock Intervals that
  returns no `expires_in` and no `refresh_token`, as in Rivera's response. The
  steps were: `auth/init` without a token returns 401, `auth/init` with a token
  returns the authorize URL, the callback connects, status shows no expiry, and
  wellness returns data.
- Expiry paths were exercised in-process against the mock: a 401 from Intervals
  marks the connection expired; a due connection with no refresh token is marked
  expired without any network call; a connection with no expiry stays connected.
- Not verified: the real Intervals authorize step (cause 2). No calls were made
  to the live service except one unintended GET to `intervals.icu/api/v1/...`
  with a dummy token (it returned 403). That was from a test script that did not
  set `INTERVALS_BASE`.

## Still needed

1. Set `INTERVALS_CLIENT_ID` and `INTERVALS_CLIENT_SECRET` in the deploy environment.
2. Confirm in Intervals that the app registration allows the requested scopes,
   including `CALENDAR:READ`. Drop any that are not allowed.
3. Have Rivera (and each athlete) click Connect again. Rivera's current
   connection is stale.
