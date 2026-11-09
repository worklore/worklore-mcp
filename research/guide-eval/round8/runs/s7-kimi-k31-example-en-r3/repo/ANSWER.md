# Intervals.icu integration: causes and fixes

## Root causes

1. **The Connect button used the wrong request type.** It was a link to
   `GET /api/intervals/auth/init`. A full-page navigation does not include the
   SPA's `Authorization: Bearer ...` header, which is added only by its fetch
   wrapper. The endpoint therefore returned 401 for every athlete. This is the
   failure captured in `logs/connect-attempt.log` on 2026-10-14 and support
   ticket #214.

   The button now calls authenticated `POST /api/intervals/auth/init` through
   the fetch wrapper. The endpoint returns `{authorize_url}`, and the SPA opens
   that URL with `window.location.assign` (`static/app.js`, `server.py`).

2. **The authorize URL requested duplicate scope areas.** `ACTIVITY:WRITE`
   already implies `ACTIVITY:READ`, and `CALENDAR:WRITE` already implies
   `CALENDAR:READ`. Naming both versions caused Intervals.icu to reject the
   authorize request before consent, which is why manually pasted links also
   stopped working after calendar access was added.

   `config.py` now requests each area once:
   `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **The backend invented a one-hour expiry.** Intervals.icu returned neither
   `expires_in` nor `refresh_token`, but `store_connection` defaulted to 3600
   seconds. The background refresher then cleared the valid token and marked
   the connection `expired, reconnect`. This directly explains Rivera's log
   entries and ticket #219; no revocation had occurred.

   Intervals.icu access tokens remain valid until revoked. The synthetic expiry,
   refresh-token fields, and background refresh loop have been removed. A real
   provider 401 now clears the access token and sets the status to
   `revoked, reconnect`; subsequent status checks show the Connect button.

## Additional protocol correction

The token exchange now posts only `client_id`, `client_secret`, and `code` to
`/api/oauth/token`, as Intervals.icu expects. The unsupported `grant_type` and
`redirect_uri` fields were removed. The athlete id and name continue to come
directly from the token response. This was a protocol mismatch in the old code,
but the supplied logs do not establish it as a cause of the reported failures.

## Which parts of the colleague's note applied

- **Part 4 applied:** authenticated POST init, a JSON `authorize_url`, and
  frontend navigation fixed the universal Connect-button 401.
- **Part 2 applied:** removing duplicate activity and calendar areas fixed the
  authorize-step rejection.
- **Part 1 applied:** no expiry or refresh machinery is used for these
  perpetual tokens; revocation is handled lazily on the first API 401.
- **Part 3 applied:** the exchange now uses only the three supported form
  fields and consumes the bundled athlete identity.
- **The callback/state guidance was already substantially implemented:** the
  callback is unauthenticated, and its HMAC-signed state carries the user id
  with a 15-minute TTL. That implementation was retained rather than rewritten
  solely to use JWT formatting. The separate account-mismatch guard was not
  needed to fix the reported failures.
- **Encryption at rest was not added here:** this repository explicitly keeps
  connections only in memory, so it has no at-rest token storage. The
  production persistent store should still encrypt these perpetual credentials.
  The note's example `SETTINGS:WRITE` scope was not added because this app does
  not use settings access.

## Verification

Python and JavaScript syntax checks passed. A local mock Intervals.icu server
and the real app HTTP handler verified the complete flow: unauthenticated init
is rejected, authenticated POST init returns a correctly scoped authorize URL,
the callback exchanges exactly the three expected fields, wellness uses the
returned athlete id and Bearer token, a token without expiry metadata remains
connected after a simulated two hours, and a provider 401 clears the token and
requires reconnect. A separate execution of the SPA click handler confirmed
that Connect sends the authenticated POST and navigates to the returned URL.
No real Intervals.icu account or external service was used.
