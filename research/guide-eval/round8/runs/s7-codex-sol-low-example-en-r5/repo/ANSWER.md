# Intervals.icu connection fix

## Causes

1. The SPA used a normal link to `GET /api/intervals/auth/init`. Document navigation did not include the app's `Authorization` header, so the endpoint returned 401 for every athlete. The October 14 log shows this directly. The SPA now makes an authenticated `POST` and navigates to the returned `authorize_url`.
2. The authorize URL requested both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. The log's 400 `invalid_request` does not identify the exact bad parameter, but these duplicate areas match Intervals' duplicate-scope rule and the timing of the calendar change. The scopes are now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. The token response shown in the September log has neither `expires_in` nor `refresh_token`. The app invented a one-hour expiry, then cleared a usable token when the background refresher ran. The connection now lasts until disconnect or an API 401; on 401 the token is cleared and status asks for reconnection.

## Colleague note

Applied: authenticated POST initialization, one scope per area, a signed short-lived state with user identity and purpose, the three-field token exchange, athlete ID from the token response, no refresh/expiry assumption, lazy 401 revocation handling, and a reconnect account-mismatch guard. The existing callback is a GET without app authorization, as required by the redirect flow.

Not applied: JWT format and encrypted persistent storage. This demo uses a signed HMAC state and keeps connections only in process memory; it has no persistent credential store to encrypt. Production storage should encrypt access tokens at rest. The note's claim that the extra token-exchange fields cause this incident is not established by the logs; they were removed to match the documented three-field request.

## Verification

`python3 -m py_compile server.py config.py` and `git diff --check` passed. Local checks passed for valid/tampered state, no synthetic expiry, and rejecting a different athlete on reconnect. A live Intervals OAuth round trip and revocation test require configured client credentials and an athlete account; neither was performed.
