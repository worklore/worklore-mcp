# Intervals.icu integration: causes and fixes

## Causes

1. **The Connect button used an authenticated endpoint through a full-page GET.** The SPA keeps its sign-in token in `localStorage` and adds it only to `fetch` requests. Clicking the old link did not send that header, so `/api/intervals/auth/init` returned 401 for everyone. This is confirmed by `logs/connect-attempt.log` and ticket #214.
2. **The authorization URL requested duplicate scope areas.** `ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE` each name the same area twice. Intervals.icu rejects that with `invalid_request` before showing consent; `:WRITE` already includes read access. This explains the failure after calendar access was added, as described in ticket #219.
3. **The backend invented a one-hour token lifetime.** Intervals.icu returns neither `refresh_token` nor `expires_in`; its access token remains valid until revoked. The old default 3600-second expiry and background refresher therefore marked Rivera’s working connection as expired after about an hour even though it had not been revoked. This is confirmed by the token response and expiry messages in `logs/connect-attempt.log`.
4. **The token exchange sent unsupported extra fields.** It included `grant_type` and `redirect_uri`, while Intervals.icu expects only `client_id`, `client_secret`, and `code`. The captured failures occur before this exchange, so this was a latent protocol mismatch rather than a demonstrated cause of those specific errors.

## Fixes

- Replaced the Connect link with a button that makes an authenticated `POST /api/intervals/auth/init`. The endpoint returns `{authorize_url}`, and the SPA redirects with `window.location.assign`.
- Changed the scope list to `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, with each area listed once.
- Limited the token exchange form to `client_id`, `client_secret`, and `code`.
- Removed the synthetic expiry, refresh-token storage, and background refresh job. Connections now remain connected until Intervals.icu actually rejects the token.
- On an Intervals.icu API 401, clear the stored access token and set the connection status to `revoked, reconnect`.

## Colleague’s note

Applied all four main findings: perpetual tokens with lazy 401 handling, non-duplicated scopes, the three-field token exchange, and authenticated POST initialization followed by a frontend redirect.

The existing signed `state` parameter already carries the user id and enforces a 15-minute TTL, so it was retained rather than rewritten as a JWT. The in-memory development store has no at-rest persistence, so the note’s encryption-at-rest recommendation does not apply here. The reconnect account-mismatch guard was not needed for the reported failures.

## Verification

A local mock-provider run verified unauthenticated init rejection, authenticated POST init, authorize URL scope validation, callback state validation, the exact token-exchange fields, connection storage without expiry or refresh metadata, a successful wellness request, and reconnect handling after a simulated revocation 401. `python3 -m py_compile server.py config.py`, `node --check static/app.js`, and `git diff --check` also passed.
