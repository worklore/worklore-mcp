# Intervals.icu connection: causes and fixes

Sources: `logs/connect-attempt.log`, `logs/support-tickets.md` (#214, #219), `server.py`, `static/app.js`.

## Why Connect fails for everyone (#214)

**Cause 1: the button is a plain link, so it cannot send the sign-in token.**
`app.js` rendered `<a href="/api/intervals/auth/init">`. The SPA adds `Authorization: Bearer` only in its `fetch` wrapper. A browser navigation does not send that header, so the server answered `401 (no Authorization header)`. This matches the log (lines 3-13) and the `unauthorized` page from the ticket.

*Fix:* `auth/init` now returns `{"url": ...}` JSON for an authenticated request. The button calls it through `api()`, then sets `location.href` to that URL (`server.py`, `static/app.js`).

**Cause 2: the authorize step is rejected with 400 `invalid_request`.**
This is what blocks the workaround of pasting the link (#219, `connect-attempt.log` section 2). Timeline:
- The authorize request asked for `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
- The calendar scopes were added on 2026-10-02 (#219). The 400 started after that.
- The one successful connection (Rivera, 2026-09-19) was made before that change.
- Changing `state` or `redirect_uri` does not change the 400 body, which points at the scope list.

*Fix:* the default scope is now `WELLNESS:READ`, the only scope the server uses (`/wellness`). It can be overridden with the `INTERVALS_SCOPES` env var. The CALENDAR scopes are removed from the default because the Intervals side may not accept them for this client.

*Not verified:* I could not test against Intervals.icu. Rules say nothing goes to an external service, so the 400 cause is inferred from timing and the log, not reproduced. If the 400 remains with `WELLNESS:READ`, the next suspect is the client itself: `config.py` has the placeholder `CLIENT_ID = "tricoach-dev"` and says the real pair is in the deploy env, but the code never reads one.

*Also changed:* all query values are now fully percent-encoded. Before, `urlencode(..., safe=":,")` left colons unescaped in `redirect_uri` (`http:%2F%2Flocalhost:8766`), which was non-standard.

## Why Rivera "expired, reconnect" an hour later (#219)

`connect-attempt.log` section 3:
- The token response had no `expires_in` and no `refresh_token`.
- `store_connection` filled in `DEFAULT_TOKEN_TTL = 3600`, so the server invented a 1-hour lifetime.
- The background refresher then marked the connection expired at 18:37, about an hour after connecting.

The provider never said the token expires. Rivera's token was not actually dead.

*Fix:*
- Use only an `expires_in` the provider sends. Otherwise `expires_at` stays `None` and the refresher skips the connection.
- A 401 from Intervals on `/wellness` is now the signal that the connection is over. It calls `mark_expired`, which sets `expired, reconnect`. Before, the card kept saying "connected" while every call failed.

## Verification

Run locally only, using a mock Intervals server on `127.0.0.1` and the app on alternate ports (8766 was already in use by another local process, which I left alone). The checks passed:
- `auth/init` returns 401 without a Bearer token and returns the authorize URL with one.
- The authorize URL has `scope=WELLNESS%3AREAD` and the decoded `redirect_uri` matches the callback.
- The callback connects the user, and the status stays connected after refresher passes when no `expires_in` was sent.
- A 401 from `/wellness` marks the connection `expired, reconnect`.
- A bad `state` returns 400.
- `app.js` passes `node --check`, and both Python files compile.

Changes are uncommitted in the working tree.

## Found but not changed (need a decision)

1. **`static/app.js` falls back to `tok-okafor`** when `localStorage` has no `tc_token`. Anyone without a token acts as C. Okafor, and Connect would attach Intervals to Okafor's account. This should be removed before onboarding more athletes.
2. **Client credentials are hardcoded placeholders.** `CLIENT_ID`, `CLIENT_SECRET`, and `APP_SECRET` are not read from the environment, despite the "real pair is in the deploy env" comment. Production may be running with placeholders, or the deploy may use a different config.
3. **The refresher holds `LOCK` during HTTP calls** (up to 15 s per connection), which blocks `status` and `wellness` for everyone. It should copy under the lock and call out without it.
4. **Connections live only in memory.** A server restart disconnects every athlete.
5. **Calendar push is not in this repo.** The README says the app pushes workouts to athletes' calendars, but no code here uses the CALENDAR scopes. If that code lives elsewhere, it needs `INTERVALS_SCOPES` set once the Intervals client is approved for those scopes.
6. **Long-lived tokens are unknown.** If Intervals starts sending `expires_in` without a `refresh_token`, athletes will need to reconnect when it runs out. The new log line `connected ... (expires_in=..., refresh_token=...)` will show which case applies.
