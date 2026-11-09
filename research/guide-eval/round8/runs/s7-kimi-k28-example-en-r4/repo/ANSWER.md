# Why the Intervals.icu connection was broken — causes and fixes

## Causes (all confirmed against code + logs/)

**1. The Connect button was a plain link, so every click 401'd.**
`static/app.js` rendered the Connect control as `<a href="/api/intervals/auth/init">`.
Clicking it is a full-page navigation, which does not send the SPA's
`Authorization: Bearer` header — that header is only attached by the fetch
wrapper, because the sign-in token lives in `localStorage`. The init handler
called `require_user()`, so every athlete landed on a white page saying
`{"error": "unauthorized"}` (`logs/connect-attempt.log` §1, ticket #214).
This is why Rivera only got through when support *pasted the link via curl*
(with the header) during the onboarding call.
**Fix:** init is now an authenticated **POST** returning `{"authorize_url"}`
as JSON (`server.py:158`); the frontend POSTs through the fetch wrapper and
then calls `window.location.assign(authorize_url)` (`static/app.js:34`). The
GET route was deleted so the broken pattern cannot recur.

**2. The scope string named two areas twice, so Intervals rejected the
authorize step with a 400.**
`SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu treats `:WRITE` as implying `:READ` and refuses a scope string
that names the same area twice ("Duplicate scope", surfaced as the generic
`{"error":"invalid_request"}` — the log notes the body does not say which
parameter it minds). This shipped with the calendar sync on 2026-10-02, which
is exactly when even the hand-pasted link stopped working
(`logs/connect-attempt.log` §2, ticket #219 second half).
**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` — the same
effective access, each area named at most once (`config.py:11`).

**3. The app assumed the token expired after an hour; Intervals tokens never
expire.**
Intervals' token response contains no `refresh_token` and no `expires_in` —
the access token lives until the athlete revokes it (see Rivera's logged
token response). The code nonetheless applied a `DEFAULT_TOKEN_TTL` of 3600 s
and ran a background refresher that, finding no refresh token on file, flipped
the connection to `expired, reconnect` exactly one hour after connect
(`logs/connect-attempt.log` §3, lines 37–40; ticket #219). Nothing was wrong
with Rivera's grant; tricoach discarded it.
**Fix:** the connection is stored with no expiry, the refresher thread,
`DEFAULT_TOKEN_TTL` and `REFRESH_INTERVAL` are deleted, and revocation is
handled lazily: the first 401 from the Intervals API clears the stored binding
and returns a reconnect prompt (`server.py:204–211`).

**4. The token exchange sent fields Intervals does not accept.**
`exchange_code` posted `grant_type` and `redirect_uri` alongside the code.
Intervals' `POST /api/oauth/token` wants only `client_id`, `client_secret`,
`code`. Rivera's September exchange succeeded anyway, so this hadn't bitten
yet, but it was gratuitously off the documented contract.
**Fix:** `exchange_code` now sends exactly those three fields
(`server.py:57–61`). The bundled `athlete: {id, name}` in the response is
stored as before, saving a who-am-I round-trip.

## Which parts of the colleague's note applied

Applied, in the note's own numbering:

- **§4 (init must be an authenticated POST returning `{authorize_url}`)** —
  direct fix for cause 1, including the diagnosis that a full-page navigation
  drops the `Authorization` header.
- **§2 ("Duplicate scope", `:WRITE` implies `:READ`)** — direct fix for
  cause 2; the note's example scope is the same shape as the new one.
- **§1 (no `refresh_token`; token lives until revoked; lazy 401 → clear the
  token and surface a reconnect prompt)** — direct fix for cause 3.
- **§3 (token exchange takes only `client_id`/`client_secret`/`code`;
  response bundles `athlete.id`)** — fix for cause 4.

Considered but not applied:

- **State as a signed JWT with `purpose` claim** — the existing
  `sign_state`/`verify_state` already implements the same idea (HMAC-signed
  user id + 15-minute TTL, `server.py:31–46`), and the callback is the only
  consumer. The note's JWT is one implementation of that pattern, so it was
  kept as-is.
- **Account-mismatch guard on reconnect** — with lazy 401 handling the whole
  binding is cleared on revocation, so there is no stale athlete id left to
  mismatch against; the guard could never fire. If a "switch Intervals
  account" feature is ever added, revisit.
- **Encrypt the token at rest** — not applicable to this codebase: state is
  in memory only (README notes prod mirrors the shape in Postgres). Worth
  enforcing there, since the token is a perpetual credential.

## Verification

No automated test suite exists in the repo, so I ran the app against a local
stub implementing the documented Intervals behavior (rejects duplicate scope
areas; rejects `grant_type`/`redirect_uri` on the token call; returns no
`refresh_token`/`expires_in`; 401s a revoked token). Full flow passes: POST
init returns an authorize URL with deduped scopes, the stubbed provider
accepts it, the callback connects the right athlete, wellness data
round-trips through the proxy, a tampered `state` is rejected, a revoked
token yields 409 "intervals access revoked, please reconnect" and clears the
binding, and reconnecting afterwards works. `node --check` passes on the
edited `static/app.js`.
