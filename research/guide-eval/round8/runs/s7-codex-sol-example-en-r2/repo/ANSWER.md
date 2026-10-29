# Intervals.icu connection failure

The logs show three causes:

1. The SPA rendered Connect as a link to `GET /api/intervals/auth/init`. A browser navigation does not carry the Bearer token held in `localStorage`, so the endpoint returned 401 for every athlete. Connect now calls an authenticated `POST` through the SPA fetch wrapper, receives `{authorize_url}`, and navigates to it.
2. The authorize URL requested both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals rejects duplicate scope areas. The scope is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. The captured provider response was a generic 400, so the logs alone do not prove which parameter it rejected; the duplicated areas match the documented behavior in the colleague's note and the calendar scope change reported in the support ticket.
3. Rivera's token response had neither `expires_in` nor `refresh_token`. The app assigned it a 3,600-second lifetime and the background refresher cleared it near that invented expiry. Intervals tokens remain usable until revoked. The invented expiry and refresh job are removed; an Intervals API 401 now clears the token and shows a reconnect status.

The callback now exchanges the code using only `client_id`, `client_secret`, and `code`, and requires an access token and athlete ID before saving. Its signed state retains a 15-minute limit, now includes an OAuth purpose, and rejects future timestamps and unknown local users. A reconnect with a different Intervals athlete ID is rejected. The signed state is an HMAC value rather than a JWT; it supplies the same identity, integrity, purpose, and time checks needed here.

## Colleague's note

Applied: authenticated POST init and JSON URL; one scope per area; no invented expiry or refresh; lazy revocation handling on API 401; the three-field token exchange; athlete ID from the token response; purpose and 15-minute limit in callback state; and the account mismatch guard.

Not applicable here: encryption at rest, because this prototype stores connections only in process memory and has no persistent token store to encrypt. Production persistent storage should encrypt the access token. The exact JWT format was unnecessary because this app already had signed state with the required checks. The note's example scopes include `SETTINGS:WRITE`, which this app does not use.

## Verification

`python3 -m unittest -v test_integration` passes local HTTP tests for authenticated POST init, unique scope areas, callback connection, wellness access, 401 revocation, account mismatch, and exchange fields. `node --check static/app.js` passes. A live Intervals consent and revoke test was not run because this workspace has placeholder client credentials and external service use was excluded.
