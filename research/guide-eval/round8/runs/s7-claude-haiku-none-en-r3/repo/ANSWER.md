# Intervals.icu connection: causes and fixes

## What was broken

### 1. Connect button always returned 401 (every athlete)

The Connect control was a plain link: `<a href="/api/intervals/auth/init">`.
A link navigation does not send the `Authorization: Bearer` header that the
SPA's fetch wrapper adds, so `auth_init` rejected every click with
`{"error": "unauthorized"}` (logs/connect-attempt.log, section 1).

**Fix:** `auth_init` now returns `{"url": ...}` as JSON. The SPA's Connect
button calls it through `api()` (so the bearer token is sent) and then sets
`location.href` to that URL (`server.py` `auth_init`, `static/app.js`).

### 2. Authorize step rejected with 400 `invalid_request`

The authorize URL in logs/connect-attempt.log (section 2) carries
`client_id=tricoach-dev`. That is the dev placeholder in `config.py`. The
comment in `config.py` says the real client pair lives in the deploy env, but
nothing read the env: `CLIENT_ID` and `CLIENT_SECRET` were hardcoded, so
production sent the placeholder. The ticket also notes that removing `state`
or changing `redirect_uri` gives the same 400, which points at client-level
configuration rather than a bad parameter.

**Fix:** `config.py` now reads `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET`,
`INTERVALS_SCOPES` and `APP_SECRET` from the environment, keeping the dev
values as defaults. The server logs a warning at startup if the placeholder
client ID is still in use.

**Not verified:** the scope list. `CALENDAR:READ` and `CALENDAR:WRITE` were
added on 2026-10-02, and the 400 started after that (support ticket #219).
If the registered Intervals client was not granted calendar scopes, the 400
persists even with the real client ID. Check the client's allowed scopes in
Intervals; this cannot be confirmed from this repo and was not tested against
Intervals.icu.

### 3. Connections marked "expired, reconnect" about an hour after connecting

The token response for T. Rivera (logs/connect-attempt.log, section 3) had no
`expires_in` and no `refresh_token`. The server then:

- set its own expiry to `DEFAULT_TOKEN_TTL = 3600` seconds, a value Intervals
  never stated;
- in the refresher, saw that expiry come due, found no refresh token, and set
  the connection to `expired, reconnect`.

So the connection was ended by a guess, not by Intervals.

**Fix:**
- Expiry is set only when the provider states `expires_in`. Otherwise
  `expires_at` is `None` and the refresher leaves the token alone.
- If Intervals later rejects the token (HTTP 401 on the wellness call), the
  connection is marked `expired, reconnect` at that point, which is the real
  signal.
- The refresher no longer holds the global lock during network calls to
  Intervals. Before, a slow token endpoint blocked every request for up to
  15 seconds.

**Not resolved:** Intervals did not return a refresh token for this client.
Whether it issues one depends on the OAuth client's configuration on the
Intervals side, which this repo cannot show. Without a refresh token, the
athlete will still need to reconnect once Intervals expires the access token.

## Other changes

- `static/app.js`: the Connect control is now a `<button>`, not a link.
- `test_server.py`: new stdlib unit tests. They run the real HTTP handler
  against a fake Intervals.icu. Run with `python3 -m unittest test_server`.
  All 5 pass on the fixed code. On the original code 4 fail (the fifth, the
  bad-state check, passes on both versions).

## What you need to do

1. Set `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET` and `APP_SECRET` in
   the deploy env. The env var names are my choice; if the deploy env already
   uses other names, change `config.py` to match. I did not deploy anything.
2. Confirm in Intervals that the OAuth client is allowed the requested scopes,
   including `CALENDAR:READ` and `CALENDAR:WRITE`. Remove any it is not
   granted, or have it granted, and re-test the authorize step.
3. Ask whether Intervals issues refresh tokens for this client. If it does
   not, expect athletes to reconnect when Intervals expires their token.
4. Athletes who were stuck (including T. Rivera) have to click Connect again
   after the deploy. Their old state was in memory and is gone on restart anyway.

## Not done

- Nothing was deployed, published or sent to Intervals.icu or any other
  external service.
- Changes are not committed.
