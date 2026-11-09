# Intervals.icu integration: causes and fixes

## Causes

1. **Connect failed for everyone because it used an unauthenticated browser navigation.** The button was a link to `GET /api/intervals/auth/init`. The SPA keeps its token in `localStorage` and adds it only to `fetch` requests, so that navigation had no `Authorization` header and the endpoint returned 401. This matches the 2026-10-14 log and ticket #214.
2. **The manually opened authorize URL was rejected because its scopes were invalid.** `ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE` each name the same area twice. Intervals.icu rejects duplicate areas; `:WRITE` already includes read access. This explains the 400 before the consent screen after calendar sync added the duplicate calendar scopes.
3. **The working connection was expired locally after one hour for no valid reason.** Intervals.icu returned neither `refresh_token` nor `expires_in`, but the app supplied a default 3600-second lifetime and ran a refresh job. With no refresh token, that job cleared the access token and demanded reconnection. The token had not actually expired or been revoked, matching T. Rivera's log and ticket #219.
4. **The token exchange used fields Intervals.icu does not expect.** It sent `grant_type` and `redirect_uri` in addition to the required `client_id`, `client_secret`, and `code`.

## Fixes

- `static/app.js` now starts OAuth with an authenticated `POST`, and `server.py` returns `{authorize_url}` as JSON. The SPA then uses `window.location.assign` to navigate to Intervals.icu.
- `config.py` now requests `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, with each area listed once.
- `server.py` sends only `client_id`, `client_secret`, and `code` to the token endpoint.
- The synthetic expiry and refresh worker are gone. A token remains connected until an API call actually returns 401; then the stored access token is cleared and status becomes `revoked, reconnect`.
- OAuth `state` is now a signed HS256 JWT containing the user id, `purpose: intervals_oauth`, and a 15-minute expiry. Signature, purpose, and expiry are checked before code exchange.
- Reconnection rejects a callback whose athlete id differs from the athlete already attached to the user.

## Which parts of the colleague's note applied

All four numbered OAuth findings applied: perpetual tokens without refresh tokens, duplicate scope areas, the three-field token exchange, and authenticated POST initialization with frontend navigation. The related guidance on signed, purpose-bound, short-lived `state`, lazy revocation handling on a 401, use of the returned athlete id, and the reconnect account-mismatch guard also applied and was implemented.

The note's encryption-at-rest advice was not applicable to this demo's in-memory token store; it remains necessary if tokens are persisted. Its suggested real-account and real-revocation verification was not performed because this task prohibited external service calls and the repository contains placeholder OAuth credentials.

## Verification

Python and JavaScript syntax checks passed. An end-to-end local test using the real HTTP handlers and a fake Intervals.icu provider verified unauthenticated-init rejection, POST initialization, unique scopes, state signature/expiry checks, the exact token request fields, callback storage, wellness retrieval, continued connection after the old one-hour cutoff, 401-to-reconnect behavior, same-athlete reconnection, athlete-mismatch rejection, and the SPA wiring.
