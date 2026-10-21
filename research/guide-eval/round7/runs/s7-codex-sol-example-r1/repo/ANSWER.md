# Intervals.icu connection failure

## Causes

1. **The Connect button always returned 401.** The SPA kept its tricoach sign-in token in `localStorage` and sent it through its `fetch` wrapper. Connect was an ordinary `<a>` navigation to `GET /api/intervals/auth/init`, so the request had no `Authorization` header. The 2026-10-14 log records that exact 401. Connect now calls authenticated `POST /api/intervals/auth/init`, receives `{authorize_url}`, and navigates to that URL.
2. **The authorize URL requested duplicate scope areas.** It included both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. The manual authorize attempt returned `invalid_request` before consent. The log does not identify the offending parameter, but the duplicate areas match the Intervals scope rule in the colleague's note. The requested scopes are now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, with each area once.
3. **The app disconnected a valid token after about an hour.** Rivera's successful token response had `access_token` and `athlete`, but neither `expires_in` nor `refresh_token`. The server invented a 3,600 second lifetime and its background task marked the connection expired. The log shows that transition; Rivera had not revoked access. Intervals tokens are now kept until an API call returns 401. That 401 clears the token, marks the connection for reconnect, and keeps the athlete ID to guard against reconnecting a different account.

## Colleague's note: what applied

- **No refresh token or expiry:** Applied. The captured token response has neither field. Removed the fabricated expiry and refresh task; handle revocation on API 401. The note's encryption-at-rest advice matters for persistent production storage, but this repository stores connections only in memory and has no at-rest token store to change.
- **Duplicate scope:** Applied. The configured authorize URL repeated two areas. The captured provider response is only `invalid_request`, so the precise provider-side reason is inferred from the scope string and the note, not proven by that response alone.
- **Token exchange fields and athlete ID:** Applied the documented three-field exchange (`client_id`, `client_secret`, `code`) and continued using `athlete.id` from the token response. The existing code also sent `grant_type` and `redirect_uri`; there is no captured exchange failure attributing a problem to those fields.
- **Authenticated POST init and callback state:** Applied. The missing header is directly shown in the log. The callback remains an unauthenticated GET and uses a signed, 15-minute state with user ID and purpose. This implementation uses an HMAC-signed payload rather than JWT; it provides the needed signature and expiry checks. Reconnection rejects a different athlete ID unless the user disconnects first.

## Verification

`python3 -m unittest discover -s tests -v` passes local HTTP flow tests for authenticated init, unique scope areas, callback exchange fields, continued connection without expiry, API 401 handling, and account mismatch protection. A live Intervals consent and revocation test was not possible with the placeholder OAuth client in `config.py` and was not attempted against an external service.
