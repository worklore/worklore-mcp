# Intervals.icu connection: causes and fixes

Sources: `logs/connect-attempt.log`, `logs/support-tickets.md`, and the code in
`server.py`, `config.py`, `static/app.js`.

## Causes

### 1. Connect button sends a GET with no auth header (every athlete)

The button was `<a href="/api/intervals/auth/init">`. That route requires
`Authorization: Bearer`, but a full-page navigation does not send the header the
SPA keeps in localStorage. Every click therefore returned `401 unauthorized`.
Evidence: `connect-attempt.log` section 1, ticket #214 ("nobody has gotten
through the button since we started onboarding").

**Fix:** `auth/init` is now an authenticated `POST` that returns
`{"authorize_url": ...}` as JSON. The button calls it with `fetch` and then does
`window.location.assign(authorize_url)`. The GET route is gone, so an old bookmarked
link returns 404.

### 2. Scope string repeats areas, so Intervals rejects the authorize step

`SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
`:WRITE` already implies `:READ`, and repeating an area is refused. The calendar
sync (shipped 2026-10-02) added the `CALENDAR:READ,CALENDAR:WRITE` pair. That is
why the September connection worked and why pasting the link also fails now
(ticket #219). `connect-attempt.log` section 2 shows the authorize step returning
`400 {"error":"invalid_request"}` for this scope.

Caveat: the real Intervals body in the log says only `invalid_request`. It does
not name the scope. The duplicate-area cause is inferred from the scope string
and the timing, and I could not confirm it against the live service (see
Verification).

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. Each area
appears once, and the capabilities are unchanged because the `:WRITE` scopes
include reads.

### 3. The app invented a one-hour expiry, then marked the athlete "expired"

The token response has no `expires_in` and no `refresh_token`
(`connect-attempt.log` section 3). `store_connection` fell back to
`DEFAULT_TOKEN_TTL = 3600`, and the background refresher then saw an expiry with
no refresh token and set the status to "expired, reconnect". That is the
"reconnect after an hour" in ticket #219. The token was never actually expiring.

**Fix:** no expiry is stored. The refresher thread, the refresh-token branch, and
`REFRESH_INTERVAL` are removed, because Intervals issues no refresh tokens.

### 4. Revocation was never detected

When the athlete revokes the app in Intervals, `/api/intervals/wellness` relayed
the 401 but left the stored connection as "connected", so the status card lied.

**Fix:** a 401 from Intervals calls `mark_revoked()`, which clears the token and
sets status `expired, reconnect`. The endpoint returns 409, and the SPA shows
the reconnect prompt.

## Colleague's note: what applied

| Point | Applied? | Reason |
|---|---|---|
| 1. No refresh_token/expiry; handle 401 lazily; clear token and prompt reconnect | **Yes**, except encryption | Matches the logs. Refresh machinery removed. Encryption at rest was not done: this repo's store is in memory (the README says prod uses Postgres, which is not in the repo). |
| 2. `:WRITE` implies `:READ`; list each area once | **Yes** | This is cause 2. I did not add `SETTINGS:WRITE`, since this app doesn't use it. |
| 3. Token exchange is "standard-lite": only `client_id`, `client_secret`, `code` | **No** | The real provider accepted the exchange with `grant_type` and `redirect_uri` present (the Sept 19 log shows success), so removing them is not needed. |
| 3. Response bundles `athlete{id,name}` | **Already in place** | `store_connection` already reads the athlete id from the response. No extra "who am I" call is made. |
| 4. Init must be an authenticated POST returning JSON; SPA calls `location.assign` | **Yes** | This is cause 1. |
| Callback `state` as a JWT with `purpose` claim and 15-min TTL | **No** | The existing HMAC-signed state already carries the user id and rejects anything older than 900 s. It is not a cause, and the format change adds nothing for this case. |
| Account-mismatch guard on reconnect | **No** | Not a cause of the reported failures. It is a reasonable follow-up. |

The colleague's note describes a different stack. I used only the parts that
match these logs.

## Verification

No requests were sent to the real intervals.icu service, and nothing was deployed.

Using a local fake provider (`INTERVALS_BASE=http://127.0.0.1:9999`) that rejects duplicate
scope areas, returns the same token shape as the September log, and answers 401
for revoked tokens:

- Before the change: `GET /api/intervals/auth/init` with no header returned 401.
  With a Bearer token it redirected to an authorize URL that the fake rejected
  with "Duplicate scope" (HTTP 400).
- After the change: `GET` init returns 404. `POST` init with a Bearer token
  returns `authorize_url`. Following it redirects to the callback, the code
  exchange succeeds, the status shows connected with the new scope, and
  `/wellness` returns 200 with no expiry in the logs.
- After the fake revokes the token: `/wellness` returns 409, the status shows
  `expired, reconnect`, and the server logs `token revoked, reconnect`.
- Unauthenticated `POST` init returns 401. `node --check` and `py_compile` pass.

Not verified, and needs a real check before shipping:

- Whether the live Intervals authorize step accepts `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`
  (the duplicate-scope cause is inferred, not confirmed).
- That `redirect_uri` `http://localhost:8766/api/intervals/callback` is the one registered with
  Intervals. The real `client_id`/`client_secret` live in the deploy env, not in the repo.
- Real revocation behaviour (the 401 path was tested only against the fake).

## Not changed, but worth doing

- `config.py` contains `APP_SECRET` and `CLIENT_SECRET` as literal values. Move them to env vars.
- Connected athletes must reconnect once after this deploy: their existing
  connections (in memory or DB) still carry the old scope and the old expiry state.
- The state-signing and token store are still in memory in this repo, so a
  restart drops every connection.
