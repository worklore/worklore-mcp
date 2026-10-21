# Intervals.icu connect: causes and fixes

## Causes

### 1. Connect fails for everyone: the button is a GET navigation (logs/connect-attempt.log §1, ticket #214)
`index.html`/`app.js` rendered `<a href="/api/intervals/auth/init">`. A full-page navigation does not send the
`Authorization: Bearer` header that the SPA's fetch wrapper adds, so `require_user()` returned 401 for every
athlete. The server log shows `GET /api/intervals/auth/init 401 (no Authorization header)`.

**Fix:** init is now an authenticated `POST` that returns `{"authorize_url": ...}` as JSON. The button calls it
through the normal `api()` wrapper, then does `window.location.assign(authorize_url)`. The GET route is removed.

### 2. Authorize step rejects the scope list (logs/connect-attempt.log §2, ticket #219)
`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. Both
`ACTIVITY:READ` and `CALENDAR:READ` repeat an area that its `:WRITE` already covers. Since calendar sync shipped on
2026-10-02, Intervals has answered the authorize URL with 400 before the consent screen (manual test on 2026-10-17
got `{"error":"invalid_request"}`).

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`: each area once. The app never reads activities
or calendar, so the `:READ` entries were not needed.

Note: the logged 400 body is the generic `invalid_request`, not the text "Duplicate scope" from the colleague's
note. The log does not show which parameter Intervals objected to. The duplicate-area explanation fits the
timeline (the 10-02 calendar change) and the rule in the note, but it is inference until the new scope string is
accepted by the real Intervals authorize endpoint (see Not verified).

### 3. Rivera "expired, reconnect" about an hour after connecting (logs/connect-attempt.log §3, ticket #219)
The token response contained no `expires_in` and no `refresh_token`. The old `store_connection` filled in
`DEFAULT_TOKEN_TTL = 3600`, so the app invented a one-hour expiry. The background refresher then marked the
connection "expired, reconnect" at 18:37, about 56 minutes after connecting. Intervals never expired that token.
The refresher and the expiry bookkeeping were the cause, not the provider.

**Fix:** tokens are stored with no expiry and the refresher thread is removed. A 401 from the Intervals API is
what marks a connection dead: `drop_connection()` clears the access token and sets `reconnect required`, and the
wellness endpoint returns 409 so the SPA can show the reconnect prompt.

### 4. Pasting the authorize link also fails
Same cause as #2: the link was built with the same invalid scope list, so pasting it hit the same 400.

## Which parts of the colleague's note applied

| Note section | Applied? | Why |
|---|---|---|
| 1. No refresh_token / no expiry; handle revocation on 401; encrypt at rest | **Yes**, except encryption | Matches the Rivera log exactly. Revocation on 401 is implemented. Encryption at rest is not: the store is in-memory, so there is nothing at rest. That changes when the Postgres tables are added. |
| 2. `"Duplicate scope"`, each area once | **Yes** | Applied to `SCOPES`. Our observed error body differs (see Cause 2). |
| 3. Token exchange "standard-lite"; take `athlete.id` from the response | **Partly** | Taking `athlete.id` from the response was already done, and it avoids a "who am I" call. I did **not** strip `grant_type` / `redirect_uri` from the exchange. The 2026-09-19 exchange succeeded with them, so the note's "wants only" rule is not confirmed for us and nothing requires the change. |
| 4. Init must be an authenticated POST (XHR), not a GET link | **Yes** | This is Cause 1. The note's description matches our logs exactly. |
| `state` as a signed JWT with `purpose` and 15-min TTL | **Partly** | `state` was already signed and had a 900s TTL. I did not add a `purpose` claim or switch to JWT: the code is stdlib-only and `state` is used for nothing else. Optional hardening. |
| Account-mismatch guard on reconnect | **No** | Not a cause of any reported failure, and it would block legitimate reconnects. Worth a decision with the product owner. |
| Reproduce / Verify steps | **Partly** | Run against a local fake Intervals (below). The live checks need real credentials and were not run. |

## What changed

- `config.py`: `SCOPES` fixed; `REFRESH_INTERVAL` removed.
- `server.py`: init moved to POST and returns JSON; expiry/refresh machinery removed; 401 from Intervals drops the
  token; `DEFAULT_TOKEN_TTL` and the refresher thread removed.
- `static/app.js`: Connect is a button that POSTs with the auth header, then navigates to `authorize_url`.

## Verified

Run against a local stand-in for Intervals (not the real service), with tricoach on a separate port:

- Old GET link: 404 (route removed). POST without a header: 401. POST with `tok-rivera`: 200 with `authorize_url`.
- Authorize (local stand-in accepts the new scopes, rejects the old duplicate scope list with 400).
- Callback: 302 to `/?connected=1`. Status: `connected`, athlete `i98765`, scope as granted.
- Wellness with the token: 200. After the stand-in revokes the token: 409, status `reconnect required`.
- The stand-in's token response has no `expires_in` or `refresh_token`; the connection stayed `connected` in every
  check. JS syntax was checked with `node --check`.

## Not verified

- **Real Intervals.icu.** I did not contact it. Confirm that `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` is
  accepted on the authorize URL with the real `client_id`, and that a real connected account gets wellness data.
- **The one-hour expiry.** The fix is verified by the code path (no expiry is set and nothing expires it), not by
  waiting an hour with a real token.
- **Revoke in Intervals settings.** The fake's revoke switch stood in for it.
- **Existing connections.** Connections are in memory, so restarting the server drops them. Rivera and anyone else
  connected before this change must reconnect.

## Running server on port 8766

A `server.py` on port 8766 was already running from another directory (`/private/tmp/h-EtQiB7`, pid 66430), with the
old code. It must be restarted to pick up these changes. I did not touch it.

## Other things I noticed (not changed)

- `static/app.js` falls back to `tok-okafor` when no token is stored, so any visitor without a token is signed in
  as C. Okafor. That is a dev default and should not reach production.
- `config.py` holds `APP_SECRET` and `CLIENT_SECRET` placeholders in source. The real pair is said to be in the
  deploy environment; check that the placeholders are not used there.
- If the athlete denies consent, Intervals redirects to the callback with `error=` and no `code`. The callback
  returns a bare 400 JSON instead of sending the user back to the app.
