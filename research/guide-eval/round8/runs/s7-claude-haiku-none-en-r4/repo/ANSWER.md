# Intervals.icu connection: causes

Evidence is in `logs/connect-attempt.log` and `logs/support-tickets.md`.

## 1. Connect button always returns `{"error": "unauthorized"}` (every athlete, ticket #214)

The button was a plain link to `/api/intervals/auth/init`. The browser's
navigation request does not carry the `Authorization: Bearer` header that the
SPA's fetch wrapper adds, so `require_user()` rejects it with 401 before the
OAuth redirect is built. Nobody could get past this button.

**Fix:** `auth_init` is now a `POST` that returns `{"url": ...}`. The SPA calls it
through `api()` (which sends the token) and then sets `location.href` to the URL.

## 2. Authorize step returns 400 `invalid_request` (since calendar sync, 2026-10-02)

The scope string gained `CALENDAR:READ,CALENDAR:WRITE` on 2026-10-02. Intervals
answers the authorize request with a 400 before the consent screen appears. The
one connection made before that date (Rivera, 2026-09-19) was granted
`ACTIVITY:WRITE,WELLNESS:READ` with no calendar scope, so the pre-calendar
request worked.

The earlier test in the log does not rule out scope. It removed `state` and
changed `redirect_uri`, and both gave the same body. It never removed or changed
the scope.

**Not confirmed:** I could not reach Intervals to check the OAuth client's
registration. Either the client is not enabled for CALENDAR scopes, or the
calendar request is malformed. Someone with access to the Intervals OAuth client
needs to check this.

**Change made:** `SCOPES` now comes from `INTERVALS_SCOPES` and defaults to the
pre-calendar set. The Connect flow works without calendar access. Calendar sync
(pushing planned workouts) is off by default, and turning it back on needs both
the Intervals-side fix above and `INTERVALS_SCOPES` including `CALENDAR:*`.

## 3. Connections expire after exactly one hour (ticket #219)

Intervals' token response has no `expires_in` and no `refresh_token`. The code
fell back to `DEFAULT_TOKEN_TTL = 3600`, so the refresher marked the connection
`expired, reconnect` one hour after connecting. The token was never checked, and
the access token was discarded. Rivera's log shows this: connected 17:41:04,
expired 18:37:12, with "no refresh token on file".

**Fix:**
- A token response with no `expires_in` now gets `expires_at = None`. The
  refresher skips it, and the connection stays `connected`.
- A 401 from Intervals on a wellness call now marks the connection
  `expired, reconnect` right away. That covers an athlete who revoked the app.
- The refresh path also no longer crashes if `expires_in` is missing (it used
  `int(tok["expires_in"])`, which raised `KeyError`).

## 4. Hardcoded OAuth client in `config.py`

`CLIENT_ID` and `CLIENT_SECRET` were fixed placeholders. The comment says the
real pair lives in the deploy env, but nothing read it. A deploy that relies on
the env would send the placeholder `tricoach-dev` to Intervals.

**Fix:** `CLIENT_ID`, `CLIENT_SECRET`, and `SCOPES` read `INTERVALS_CLIENT_ID`,
`INTERVALS_CLIENT_SECRET`, and `INTERVALS_SCOPES`, falling back to the existing
values. If the deploy already overrides `config.py`, this changes nothing there.

## Not changed (noticed while fixing)

- `static/app.js` falls back to the `tok-okafor` dev token when nothing is
  stored in `localStorage`. Every browser with no token signs in as C. Okafor.
  This is documented as dev-only, but it is risky if the SPA is served anywhere real.
- `disconnect` only drops the connection locally. Nothing tells Intervals to
  revoke the token, so tricoach stays listed under the athlete's Intervals apps
  (ticket #219). There is no revoke call in the code.
- The refresher holds `LOCK` during the token HTTP calls (up to 15 s each), which
  blocks every request while it runs.
- All state is in memory, so connections are lost on restart.

## Verified

- `python3 -m py_compile` on both Python files and `node --check` on `app.js`
  pass.
- Running the server locally: `GET /api/intervals/auth/init` returns 404;
  `POST` without a token returns 401; `POST` with a token returns 200 and an
  authorize URL with the state parameter.
- A Rivera-style token (no `expires_in`) stays connected after simulating 10
  hours. A token with `expires_in` gets the correct expiry.
- Not tested end to end: the real Intervals authorize, callback, and token
  exchange. I could not reach Intervals from here, so cause 2 remains open.
