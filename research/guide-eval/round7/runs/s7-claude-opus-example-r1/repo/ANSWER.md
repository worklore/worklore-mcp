# Intervals.icu connection: causes and fix

Three separate faults. Each one shows up in a different part of `logs/`.

## 1. Connect button: 401 for everyone (ticket #214, log §1)

The button was a plain `<a href="/api/intervals/auth/init">`, and the server's init handler was a `GET` that needs `Authorization: Bearer`. The SPA keeps its token in `localStorage`, and only its `fetch` wrapper sends it. A link click is a full-page navigation, so the browser sends no Authorization header (log §1 shows only `Accept`/`Referer`), and `require_user()` returns `401 {"error":"unauthorized"}`. The support workaround of pasting a link built with curl only worked because curl added the header by hand.

**Fix:** `/api/intervals/auth/init` is now an authenticated `POST` that returns `{"authorize_url": ...}` as JSON (`server.py`). The button calls it through `api()` and then does `window.location.assign(authorize_url)` (`static/app.js`). `GET` on that path now returns 404.

## 2. Authorize step: 400 `invalid_request` (ticket #219, log §2)

`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. That asks for ACTIVITY twice and CALENDAR twice. In Intervals, `:WRITE` already includes `:READ`, and it rejects a scope that names the same area twice. Rivera's working grant on 2026-09-19 (`ACTIVITY:WRITE,WELLNESS:READ`) named each area once. The authorize step broke when calendar sync changed the scope string. The log also notes that removing `state` or changing `redirect_uri` gives the same 400, which leaves `scope` as the parameter at fault.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` (each area once; WRITE where the app writes).

Caveat: our capture shows a bare `invalid_request`, not the `Duplicate scope` text the colleague's note mentions. So this cause is inferred from the evidence above. It has not been confirmed against the real Intervals.icu service. The first real connect will confirm it.

## 3. "Expired, reconnect" about an hour after connecting (ticket #219, log §3)

Intervals tokens have no `expires_in` and no `refresh_token`; they stay valid until the athlete revokes the app. `store_connection()` filled the missing value with `DEFAULT_TOKEN_TTL = 3600`. The background refresher then found no refresh token, set the status to `expired, reconnect`, and **threw away a valid token** (`access_token=None`). That's why Rivera, who never revoked anything, was told to reconnect.

**Fix:** with no `expires_in`, `expires_at` is now `None`, and the refresher skips those connections. Revocation is detected lazily instead. When `/api/intervals/wellness` gets a 401 from Intervals, it clears the token, sets the status to `revoked, reconnect`, and returns 409. The card then shows the reconnect prompt instead of an error.

Prod note: rows already marked `expired, reconnect` have had their token cleared, so those athletes (Rivera) have to click Connect once more. With fixes 1 and 2 in place, that now works.

## Also added

- **Account-mismatch guard in the callback:** if a user who is already linked to athlete X comes back with athlete Y, the callback returns 409 ("disconnect first") instead of silently replacing the link.

## Verification

I ran `server.py` with `INTERVALS_BASE` pointed at a local fake Intervals server (in `/tmp/h-test`, outside the repo). The fake rejects scopes that repeat an area, returns token responses without `expires_in`/`refresh_token`, and can be switched to revoked. Results:

- `GET` init → 404.
- `POST` init → `authorize_url` with the new scope.
- Authorize → callback → `/?connected=1`.
- Status: connected, with "no expiry; valid until revoked" in the log.
- Wellness → 200 with data.
- After revoking: wellness → 409 `revoked, reconnect`, and the status matches.

The fake encodes my assumptions about Intervals, so this checks the app's own logic, not Intervals itself. I didn't contact the real service.

## The colleague's note: what applied

- **§4 (init must be POST, return `{authorize_url}`, front end calls `location.assign`):** applied. This is cause 1, and the log matches the note's symptom exactly.
- **§2 (`Duplicate scope`; `:WRITE` implies `:READ`, each area once):** applied as cause 2. As said above, our error text is `invalid_request`, not `Duplicate scope`. I used the note's rule, not its scope string: `SETTINGS:WRITE` is something the note's app needed, and tricoach doesn't use it.
- **§1 (no refresh/expiry; handle 401 lazily by clearing the token and prompting a reconnect):** applied. This is cause 3.
- **§1 (encrypt the token at rest):** not done here. This repo stores everything in memory. It's still advisable for the prod Postgres table, since the token never expires.
- **§3 (token exchange takes only `client_id`/`client_secret`/`code`):** not applied. Our exchange also sends `grant_type` and `redirect_uri`, and Rivera's exchange on 09-19 succeeded with them. Nothing in the logs points at the exchange, so I left it alone. `athlete.id` is already read from the token response.
- **State JWT with `purpose` claim, 15-min TTL:** not needed. The existing HMAC-signed `user_id:timestamp` state with a 900 s max age already covers identity and TTL, and the state is used for nothing else. The **account-mismatch guard** from the same paragraph was added.
- **"Reproduce this" steps (forum registration, testing against a real account, deliberately sending a duplicate scope to Intervals):** not done. They need real credentials and an external service, which is outside this task's ground rules.
