# Intervals.icu connection failure

## Causes found

1. The SPA used a normal link to `GET /api/intervals/auth/init`. A page navigation does not carry the `Authorization` header from the SPA's fetch wrapper, so the endpoint returned 401 for every athlete. The request and missing header are recorded in `logs/connect-attempt.log`.
2. The authorize URL requested both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. The captured authorize request returned 400 before consent. Intervals' rule that `:WRITE` includes `:READ` makes these duplicate areas the likely cause; the generic `invalid_request` body alone does not prove which parameter failed.
3. The successful September token response had neither `expires_in` nor `refresh_token`. Our code invented a 3,600-second expiry, then its background worker cleared the token and demanded reconnection. The log shows this happening to Rivera even though the token had worked for wellness and the athlete had not revoked access.

## Fix

- The button now calls authenticated `POST /api/intervals/auth/init` through the SPA fetch wrapper, receives `{authorize_url}`, and navigates to it. The scopes now name each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
- The callback validates a signed, 15-minute state containing the tricoach user and OAuth purpose, then exchanges the code with `client_id`, `client_secret`, and `code`. It stores the returned athlete ID and token without a fabricated expiry. Reconnecting to a different Intervals athlete requires an explicit disconnect first.
- The wellness proxy keeps using the Bearer token. On an Intervals 401, it clears that token and marks the connection for reconnection. OAuth settings can now come from environment variables (`INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET`, `INTERVALS_REDIRECT_URI`, `APP_SECRET`).

## Colleague's note

The POST init pattern, unique scope areas, minimal token exchange, absence of token refresh, signed callback state, athlete ID from the token response, Bearer API calls, 401 revocation handling, and reconnect identity guard all applied. The note proposes a JWT for state; this implementation uses an HMAC-signed state with the same subject, purpose, and expiry checks, without a JWT dependency. Its encryption-at-rest advice applies to persistent production storage; this repository stores connections only in memory, so there is no token file or database here to encrypt. Its example scope list includes `SETTINGS:WRITE`, which this app does not use.

## Verification

`python3 -m unittest -v test_integration.py` passes. The local test covers authenticated initiation, scope and token exchange parameters, callback, wellness, 401 revocation, status, and athlete mismatch. A real Intervals account and production client credentials were unavailable here, so live consent and API behavior were not verified.
