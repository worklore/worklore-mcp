# Intervals.icu connection failure

## Causes

1. The Connect control was a document navigation to `GET /api/intervals/auth/init`. Document navigations do not carry the SPA's `Authorization` header, so the authenticated endpoint returned 401 for every athlete. This matches `logs/connect-attempt.log` and support ticket #214.
2. The authorize URL requested both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals.icu permits one permission per area; `WRITE` includes `READ`. The resulting duplicate areas caused the authorize request to fail before consent, matching the later manual-link attempt in the logs. The provider's [OAuth announcement](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) documents the scope behavior.
3. The token response had neither `expires_in` nor `refresh_token`, but the backend invented a 3,600-second lifetime. Its refresher then cleared the working token, causing Rivera's reconnect prompt. The token response and subsequent expiry log show this directly. Intervals.icu's [OAuth announcement](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) also says its OAuth tokens do not use refresh tokens.
4. The configured client ID, client secret, and callback URI were hardcoded development values despite the README saying production supplies them through the environment. The deployment would therefore be unable to use its registered OAuth client unless its files were modified separately.

## Fix

- Connect now calls authenticated `POST /api/intervals/auth/init` through the SPA's fetch wrapper, receives `{authorize_url}`, and navigates to it. The callback remains an unauthenticated GET. Its signed state carries the app user, purpose, and issue time, with a 15-minute limit.
- The requested scopes are `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
- Code exchange sends `client_id`, `client_secret`, and `code`. The connection uses `athlete.id` from the response. No synthetic expiry or refresh job remains. A 401 from the Intervals wellness API clears the access token and marks the connection as needing reconnection.
- Reconnecting a different Intervals athlete to an existing app account is rejected. The OAuth client settings and callback URI can now be supplied with `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET`, and `INTERVALS_REDIRECT_URI`; `APP_SECRET` can also be supplied through the environment.

## Colleague note: what applied

The no-refresh-token behavior, unique scope rule, minimal token exchange, authenticated POST init, unauthenticated callback with signed short-lived state, and account-mismatch guard all applied. This implementation uses its existing HMAC-signed state format rather than a JWT; the required identity, purpose, and age checks are present. The note's encryption-at-rest advice is for persisted credentials: this repository only stores connections in memory and has no database storage layer to change. Its API 401 handling was added for the existing wellness proxy.

## Verification and limit

`python3 -m unittest -v test_intervals.py` passes local HTTP flow tests for init authentication and scopes, callback token exchange, revocation handling, account mismatch, and state tampering/expiry. No real Intervals account or production credentials are available here, so live consent and wellness retrieval were not exercised. Production must set the registered client values and a stable secret in its environment.
