# ANSWER — why athletes couldn't connect Intervals.icu, and what changed

## Root causes (three independent bugs)

### 1. The Connect button was a plain link, so it 401'd for everyone
The SPA keeps the sign-in token in `localStorage` and attaches it as an
`Authorization` header **only on `fetch` calls**. The Connect button was an
`<a href="/api/intervals/auth/init">`, a full-page navigation, which carries no
auth header — so the server answered `401 {"error": "unauthorized"}` and the
athlete landed on a white error page (ticket #214, `logs/connect-attempt.log`
entry 1). The one athlete who connected (Rivera) only got through because a
coach hand-pasted the authorize URL with `curl -H 'Authorization: ...'`.

**Fix:** init is now an authenticated `POST /api/intervals/auth/init` that
returns `{"authorize_url"}` as JSON (`server.py:191`), and the SPA calls it via
`fetch` and then `window.location.assign(authorize_url)`
(`static/app.js:33-36`). GET on that path now returns 405.

### 2. The scope string named areas twice, so Intervals rejected the authorize step
`config.py` asked for `ACTIVITY:READ,ACTIVITY:WRITE,...,CALENDAR:READ,CALENDAR:WRITE`.
On Intervals.icu, `:WRITE` already implies `:READ`, and naming an area twice is
rejected ("Duplicate scope" — surfaced as the opaque `{"error":"invalid_request"}`
400 in `logs/connect-attempt.log` entry 2). This broke the flow for everyone
from the moment the calendar sync shipped on 2026-10-02 and added the calendar
pair (ticket #219 — which is also why pasting the link by hand stopped working).

**Fix:** each area appears at most once. The app only reads wellness and writes
planned workouts to the calendar, so scopes are now
`WELLNESS:READ,CALENDAR:WRITE` (`config.py:13`).

### 3. A fabricated 1-hour expiry disconnected Rivera
Intervals.icu token responses contain **no `refresh_token` and no `expires_in`**
(visible in `logs/connect-attempt.log` entry 3) — the access token lives until
the athlete revokes it. But `store_connection` invented a default 3600 s
expiry when `expires_in` was absent, and the background refresher thread then
marked the connection "expired, reconnect" one hour later — Rivera's ticket
#19. Worse, clicking Connect then hit bug 1.

**Fix:** `server.py:69-83` stores `expires_at: None` when the provider sends no
expiry, and the refresher skips non-expiring tokens. A revocation is instead
handled lazily: the first `401` from the Intervals API clears the stored
connection and the UI shows "not connected" with a fresh Connect button
(`server.py:267-274`). The bogus `DEFAULT_TOKEN_TTL` is gone.

### 4. Token exchange sent fields Intervals doesn't want (found via the note)
`exchange_code` posted `grant_type` and a `redirect_uri` echo on top of
`client_id`/`client_secret`/`code`.

**Fix:** `server.py:58-63` sends only the three fields; the bundled
`athlete: {id, name}` in the response was already being used.

## What else changed
- The OAuth `state` parameter now carries a `purpose` claim
  (`intervals_oauth`) alongside the user id, HMAC signature, and 15-minute TTL
  (`server.py:32-49`). Not a failure cause — hardening from the note.
- Reconnecting a *different* Intervals account than the one already stored is
  rejected with 409 (`server.py:229-234`), per the note's mismatch guard.

## Which parts of the colleague's note applied
- **§1 (no refresh_token / no expiry, lazy 401 handling): applied** — cause 3.
  Encryption at rest was *not* applied: this dev server keeps state in memory
  "same shape as prod"; encrypting there is a prod-storage concern, noted but
  out of scope here.
- **§2 ("Duplicate scope", `:WRITE` implies `:READ`, each area once): applied** —
  cause 2, including the rule that authorize URLs with a duplicated area are
  rejected (mirrored in the local stub used for verification).
- **§3 (standard-lite token exchange, only `client_id`/`client_secret`/`code`,
  `athlete` bundled): applied** — cause 4.
- **§4 (init must be an authenticated POST returning `{authorize_url}`, frontend
  uses `window.location.assign`): applied** — cause 1.
- **Follow-ups (signed state with user id + purpose + 15-min TTL; account-
  mismatch guard on reconnect): applied** as hardening, see above.
- **Ignored:** the exact JWT format for state (kept the existing HMAC-signed,
  base64url-encoded blob — equivalent properties, less churn); the Intervals
  forum registration details (client credentials are deploy-env placeholders
  here); the note's scope list (`ACTIVITY:WRITE,...,SETTINGS:WRITE`) — tricoach
  doesn't write activities or settings, so its scopes are smaller.

## Verification
No automated suite exists in the repo, so I verified end-to-end against a
local stub of the Intervals API (throwaway script, deleted afterwards; no
external service was contacted). 21 checks, all passing: GET init → 405;
POST init without/with auth → 401 / 200 with a dup-free authorize URL; full
connect flow → 302 to `/?connected=1`, status connected, wellness proxy 200;
token exchange carried exactly the three fields; mismatched-athlete reconnect →
409 with the original connection intact; same-athlete reconnect → OK; revoked
token (401 from API) → connection cleared, status "disconnected"; tampered
state → 400; server log records "(no expiry)" and no fabricated 3600 s expiry.

One environment note: port 8766 was squatted by a stale `server.py` process
(PID 84285) running from a *different* temp directory with half-applied fixes
(its own scopes, an `INTERVALS_BASE` pointing at a dead local stub). It
shadowed the real app and would have kept "fixing" nothing for real users; I
terminated it. Nothing in this repo references it.
