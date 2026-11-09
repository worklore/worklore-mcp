# Intervals.icu integration: causes and fixes

## Causes

1. **The Connect button used an unauthenticated full-page GET.** The SPA keeps its sign-in token in `localStorage` and adds it only in the `fetch` wrapper. Clicking the old `<a href="/api/intervals/auth/init">` did not use that wrapper, so the request had no `Authorization` header and the server returned 401. This is the universal failure captured in `logs/connect-attempt.log:3-13` and support ticket #214.
2. **The authorize URL requested duplicate scope areas.** `ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE` each name the same area twice. Intervals.icu rejects that with `Duplicate scope` (surfaced by the app as the logged `invalid_request`), before consent. `:WRITE` already includes read access. This explains why manually pasted authorize links also failed after calendar access was added.
3. **The app invented a one-hour token lifetime.** Intervals.icu returns neither `refresh_token` nor `expires_in`; its access token remains valid until revoked. The old code substituted a 3600-second TTL and then cleared Rivera’s still-valid token when no refresh token existed. This caused the erroneous `expired, reconnect` state in `logs/connect-attempt.log:35-40` and ticket #219.
4. **The token exchange contained unsupported fields.** It sent `grant_type` and `redirect_uri` in addition to the required credentials and code. Intervals.icu’s exchange expects only `client_id`, `client_secret`, and `code`. The captured successful response does not establish that these extra fields caused either reported outage, but this was an additional incompatibility and is now corrected.

## Changes

- `static/app.js` turns Connect into a button that makes an authenticated `POST /api/intervals/auth/init`, then passes the returned `authorize_url` to `window.location.assign`.
- `server.py` accepts init only as POST and returns `{authorize_url}` as JSON rather than redirecting a GET.
- `config.py` now requests `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, with each area listed once.
- `server.py` sends exactly `client_id`, `client_secret`, and `code` to the token endpoint and stores the athlete identity returned with the token.
- Token expiry and refresh machinery is removed. Connections no longer have `expires_at` or `refresh_token` fields and are not disconnected after an hour.
- A real 401 from the Intervals API now clears the access token and changes the connection to `revoked, reconnect`; the existing UI then offers Connect again.
- OAuth state remains HMAC-signed with a 15-minute TTL and now also carries and validates the `intervals_oauth` purpose. Reconnect callbacks reject a different athlete ID instead of replacing the existing athlete association.

## Which parts of the colleague’s note applied

- **Applied:** perpetual tokens with no refresh flow; lazy revocation handling on API 401; one scope entry per area; the three-field token exchange; using the token response’s athlete ID; authenticated POST init returning JSON followed by SPA navigation; signed, time-limited, purpose-bound state; and the reconnect athlete-mismatch guard.
- **Not applied literally:** the note’s example `SETTINGS:WRITE` scope was omitted because this app has no settings integration. Token encryption at rest is not applicable to this repository’s in-memory store; persistent production storage should still encrypt these perpetual credentials. The existing stdlib HMAC state mechanism was retained rather than replaced specifically with a JWT.
- **Verification limits:** the note’s real-account/provider checks were not run because verification was kept local. A mock Intervals.icu HTTP server verified duplicate-scope rejection, the exact exchange fields, callback and wellness behavior, revocation, and reconnect.

## Local verification

- Python parsing, JavaScript syntax, and `git diff --check` passed.
- An end-to-end local HTTP flow passed: authenticated POST init, authorize redirect, callback/token exchange, connected status, and wellness retrieval.
- Simulated revocation returned 401, cleared the token, and exposed `revoked, reconnect`; same-athlete reconnect succeeded and a different athlete was rejected with 409.
- A DOM/fetch check of the actual `static/app.js` confirmed that Connect sends the bearer token via POST and navigates to the returned authorize URL.
