# Intervals.icu integration — root causes and fixes

## Causes (three independent bugs)

1. **The Connect button did a full-page GET, which cannot carry auth.**
   `static/app.js` rendered "Connect Intervals.icu" as a plain
   `<a href="/api/intervals/auth/init">`. A document navigation sends no
   `Authorization` header — the SPA's sign-in token lives in localStorage and
   only travels on `fetch` calls — so `require_user` answered 401 for every
   athlete before an authorize URL was ever built. This is the white page with
   `{"error": "unauthorized"}` in `logs/connect-attempt.log` §1 and ticket
   #214. (The one athlete who got through, Rivera, was connected by pasting
   the URL by hand — which bypassed the button but hit cause 2 after the
   calendar scope shipped.)

2. **The authorize request named the same scope area twice.**
   `config.py` had
   `SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`.
   Intervals.icu treats `:WRITE` as implying `:READ` and rejects a scope that
   lists one area twice with `400 {"error": "invalid_request"}` *before* the
   consent screen. The log (`connect-attempt.log` §2) shows this for the
   hand-built link, and ticket #219 dates it: the integration asked for
   calendar access when calendar sync shipped on 2026-10-02, creating the
   `CALENDAR:READ` + `CALENDAR:WRITE` pair (and `ACTIVITY:READ` +
   `ACTIVITY:WRITE` was already there). So even the paste-the-link workaround
   broke that day.

3. **The code fabricated a one-hour expiry for a token that never expires.**
   The token response from Intervals.icu contains no `refresh_token` and no
   `expires_in` — the access token lives until the athlete revokes it. But
   `store_connection` substituted a made-up 3600 s TTL when the provider
   "didn't say", and the background refresher then flipped the connection to
   "expired, reconnect" when that TTL passed, with no refresh token to renew
   it. `connect-attempt.log` §3 shows exactly this for Rivera: connected at
   17:41, marked "expired, reconnect" at 18:37 without any revocation —
   hence the "reconnect after an hour" instruction in ticket #219.

## Fixes

- `server.py` / `static/app.js` — `POST /api/intervals/auth/init` now returns
  `{"authorize_url"}` as JSON; the SPA POSTs via `fetch` (so the
  `Authorization` header travels) and then calls
  `window.location.assign(authorize_url)`. The GET route is gone, so the
  button can no longer 401.
- `config.py` — `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`
  (each area exactly once; `:WRITE` where tricoach writes, `:READ` for the
  wellness read-only area).
- `server.py` — the connection is stored with no expiry and the token
  refresher is removed entirely (there is nothing to refresh). Revocation is
  handled lazily: the first 401 from the Intervals API clears the stored
  token and marks the user "expired, reconnect", and reconnecting runs the
  normal OAuth flow again.
- `server.py` — the token exchange now posts only `client_id`,
  `client_secret`, `code` to `/api/oauth/token` (no `grant_type`, no
  `redirect_uri` echo). The bundled `athlete.id` was already stored and used
  for all API paths.

## Colleague's note — which parts applied

- **§4 "the init endpoint must be POST"** — applied, this is cause 1. The
  note's same-day rewrite (authenticated POST returning `{authorize_url}`, SPA
  does `window.location.assign`) is exactly what was implemented.
- **§2 "Duplicate scope"** — applied, this is cause 2. `:WRITE` implies
  `:READ`; each area at most once.
- **§1 "no refresh_token; handle revocation lazily on the first 401"** —
  applied, this is cause 3. The fabricated TTL and refresher were removed;
  a 401 from the API now degrades to a reconnect prompt instead of a crash.
  The note's "encrypt at rest" advice was **not** applied: this app's store
  is in-memory only, so there is nothing at rest to encrypt.
- **§3 "token exchange is standard-lite"** — applied to the exchange call
  (only `client_id`, `client_secret`, `code`; athlete id bundled). It was not
  itself an observed failure cause (the September exchange in the log
  succeeded even with the extra fields), but it was aligned with the
  documented provider behavior.
- **JWT `state` with `purpose` claim** — not applied. The existing state is
  already an HMAC-signed, timestamped blob with a 15-minute TTL carrying the
  user id, and it correctly authenticated the callback in the one working
  connection. Not a failure cause, so left as is.
- **Account-mismatch guard on reconnect** — not applied. There is one
  connection slot per user and reconnecting overwrites it; no ticket pointed
  at this.

## Verification

No external service was contacted: a local stub emulated the documented
Intervals.icu behavior (token response without `refresh_token`/`expires_in`,
401 after "revocation"). Against it, with the real server:

1. `POST /api/intervals/auth/init` with the Bearer token → 200 and an
   `authorize_url` whose scope is `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`
   (each area once, signed `state` present). The old `GET` on that path now
   404s.
2. `GET /api/intervals/callback?code=...&state=...` → 302 to `/?connected=1`;
   `/api/intervals/status` → `connected: true` as athlete `i999`.
3. `GET /api/intervals/wellness` proxied through with the Bearer token → 200
   with wellness data.
4. Simulated revocation (stub starts 401ing) → wellness returns 401 and
   status flips to `"expired, reconnect"` without a crash.
5. Reconnect: `POST init` → callback again → `connected: true` again.
6. Regression check for cause 3: the connection is still `connected` after
   well past a refresher-interval of time with no expiry scheduled anywhere —
   the fabricated one-hour death cannot recur. The stub also logged that the
   token exchange carried exactly `client_id`, `client_secret`, `code`.
