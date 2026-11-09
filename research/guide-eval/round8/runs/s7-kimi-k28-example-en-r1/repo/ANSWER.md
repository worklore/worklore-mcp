# Intervals.icu integration — causes and fixes

The integration had three independent bugs, matching the three symptoms in
`logs/connect-attempt.log` and `logs/support-tickets.md`.

## Causes

### 1. Connect button 401'd for every athlete (`auth/init` reached via plain link)

The SPA rendered the Connect button as `<a href="/api/intervals/auth/init">`
(`static/app.js`). A full-page navigation does **not** carry the
`Authorization: Bearer` header — the SPA's token lives in localStorage and is
only attached by its fetch wrapper. The server required auth on `auth_init`,
so every click ended on a white page `{"error": "unauthorized"}`
(log §1, ticket #214). Nobody could get through the button; Rivera's onboarding
only worked because the coach pasted the authorize URL into the browser by hand.

**Fix:** `init` is now an authenticated **POST** that returns
`{authorize_url}` as JSON (`server.py`, `auth_init` in `do_POST`), and the SPA
POSTs it and then calls `window.location.assign(authorize_url)`
(`static/app.js`). The GET route is gone, so the flow can't regress.

### 2. Authorize step 400'd before the consent screen ("Duplicate scope")

`config.SCOPES` was
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE` —
`ACTIVITY` and `CALENDAR` were each named twice. Intervals.icu rejects a scope
string that names the same area twice (`:WRITE` already implies `:READ`),
answering the authorize request with an error page before any consent screen
(log §2, ticket #219). This started on 2026-10-02, when the calendar sync added
the duplicated `CALENDAR:READ,CALENDAR:WRITE` pair, breaking even the
paste-the-link workaround.

**Fix:** each area at most once:
`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

### 3. Valid connections killed after an hour ("expired, reconnect")

The Intervals.icu token response has **no `refresh_token` and no `expires_in`**
— the access token lives until the athlete revokes it. The backend invented a
3600 s default TTL (`DEFAULT_TOKEN_TTL`) and a background refresher marked any
token without a refresh token as `"expired, reconnect"` when that TTL passed.
Rivera's connection was therefore killed ~1 h after onboarding despite being
fully valid on the Intervals side (log §3, ticket #219) — the "reconnect after
an hour" instruction.

**Fix:** tokens are stored as perpetual credentials; the refresher thread,
`REFRESH_INTERVAL`, and all expiry bookkeeping are deleted. Revocation is
handled lazily: the first **401** from the Intervals API clears the stored
connection and the UI falls back to the reconnect prompt (tested: simulated
revocation → `wellness` 409 → `status` shows `disconnected`).

## Also changed (hardening, per the note)

- **Token exchange** now sends only `client_id`, `client_secret`, `code` — no
  `grant_type`, no `redirect_uri` echo.
- **`state` parameter** gained a `purpose` claim (payload
  `user_id:intervals_oauth:timestamp`, still HMAC-signed, 15-minute TTL).
- **Account-mismatch guard:** on reconnect, a callback whose athlete id differs
  from the one already stored is rejected with 409 and does not overwrite the
  existing connection.

## Which parts of the colleague's note applied

- **§1 — token never expires/refreshes; lazy 401 handling:** applied; the fix
  for cause 3. ("Encrypt at rest" was *not* applied: this dev harness stores
  tokens in memory with the prod table shape and has no key management — noted
  as a prod hardening item.)
- **§2 — "Duplicate scope":** applied; the fix for cause 2.
- **§3 — exchange wants only client_id/secret/code:** applied (exchange
  aligned, verified against a strict fake). The bundled `athlete: {id, name}`
  was already consumed.
- **§4 — init must be an authenticated POST returning `{authorize_url}`:** applied;
  the fix for cause 1 (their "self-inflicted" bug was exactly ours).
- **Follow-up — state with purpose claim + TTL, account-mismatch guard:**
  applied both.
- **Ignored:** nothing else was applicable — the JWT-format state (we kept the
  existing HMAC payload, just added `purpose`), the forum/registration links,
  and the generic reproduction steps.

## Verification

End-to-end against a strict fake Intervals.icu (via the `INTERVALS_BASE` env
var, since the real client credentials are placeholders): 19 checks covering
init POST (200 with `authorize_url`, 401 without auth, GET gone), scope
(un-duplicated), state (signature, purpose, TTL; bad and expired states
rejected), full connect flow (302 → status connected → wellness proxy),
account-mismatch 409 with original connection preserved, exchange request
carrying exactly the three fields, and lazy revocation on a simulated 401.
All 19 pass.
