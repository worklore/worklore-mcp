# Intervals.icu connection failures

1. **The Connect button dropped the app's sign-in token.** It was a document link to `GET /api/intervals/auth/init`, but the token lives in `localStorage` and is only added by the SPA's `fetch` wrapper. The server correctly returned 401, as shown in `logs/connect-attempt.log`. Connect now calls an authenticated `POST` and navigates to the returned `authorize_url`.
2. **The consent request repeated scope areas.** `ACTIVITY:READ` appeared alongside `ACTIVITY:WRITE`, and `CALENDAR:READ` alongside `CALENDAR:WRITE`. Intervals treats write as including read and rejects duplicate areas. The scopes now list each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. This explains the 400 after the authorize URL was pasted manually.
3. **The server invented a one-hour token expiry.** Intervals' token response in the log had no `expires_in` or `refresh_token`. The background refresher assigned a 3600-second lifetime and then cleared a valid token, causing Rivera's reconnect prompt. Connections now stay active until an Intervals API call returns 401; that response clears the token and marks the connection for reconnection.
4. **The token exchange included unsupported fields.** The server sent `grant_type` and `redirect_uri`; the Intervals exchange uses `client_id`, `client_secret`, and `code`. The request now contains those three fields only. This was a latent failure for new callbacks, separate from the logged button and scope failures.

The callback continues to validate signed, time-limited state. Reconnecting with a different Intervals athlete is rejected until the existing connection is explicitly disconnected.

Verified locally with `python3 -m unittest -v test_intervals` (four tests). The tests mock Intervals responses; no live OAuth credentials or external calls were used.
