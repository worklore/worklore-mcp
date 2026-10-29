# Intervals.icu connection fix

## Causes

1. **The Connect button always got a 401.** The SPA rendered a normal link to `GET /api/intervals/auth/init`. That full-page navigation did not carry the bearer token held in `localStorage`, while the endpoint required it. The 2026-10-14 log shows the missing `Authorization` header. Connect now calls an authenticated `POST` through the SPA's fetch wrapper, receives `{authorize_url}`, and navigates to it.
2. **The authorize request asked for duplicate scope areas.** `ACTIVITY:READ` appeared alongside `ACTIVITY:WRITE`, and `CALENDAR:READ` alongside `CALENDAR:WRITE`. Intervals.icu treats `WRITE` as including `READ`; the redundant areas explain the authorize-step failure after calendar access was added. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. The captured 400 body was only `invalid_request`, so the log alone does not prove which parameter Intervals rejected; this diagnosis also relies on the duplicated scopes and the provider's scope rules.
3. **The server invented a one-hour token expiry.** Rivera's successful token response had neither `expires_in` nor `refresh_token`. The old code assigned a 3,600-second lifetime and its background refresher then cleared the token. Intervals.icu access tokens have no scheduled refresh in this flow. The connection now remains active until an API call returns 401, at which point the token is cleared and the status becomes `reconnect`.

## Colleague's note: what applied

- **Applied:** authenticated POST initialization; one scope entry per area with `WRITE` implying `READ`; token exchange with `client_id`, `client_secret`, and `code`; use of the token response's `athlete.id`; no assumed expiry or refresh; bearer-token API calls; clearing a revoked token on 401; signed, time-limited state for the unauthenticated callback; and rejection when a reconnect returns a different athlete.
- **Adapted:** state is an HMAC-signed payload with user ID, purpose, and a 15-minute age check, using only the Python standard library rather than a JWT dependency. This app stores connections only in memory, so there is no token at rest here to encrypt. Production's persistent token column should be encrypted at rest.
- **Not applied:** the note's exact scope list includes `SETTINGS:WRITE`, which this app does not need. Its suggested real-account and revocation checks were not run because this workspace has placeholder OAuth credentials and the task forbids sending data to external services.

The provider's [OAuth guide](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) documents the token exchange fields, response shape, bearer authentication, and `WRITE` implying `READ`.

## Verification

`python3 -m unittest -v test_intervals.py` passes. Local HTTP tests cover authenticated initialization, scopes, callback storage, token-exchange fields, state expiry, 401 revocation handling, and the account mismatch guard. `node --check static/app.js` and Python compilation pass. No live Intervals.icu account was used.
