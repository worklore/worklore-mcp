# Intervals.icu connection: causes and fixes

Three separate faults, one per symptom in `logs/support-tickets.md`.

## Causes

### 1. "Connect" returns `{"error": "unauthorized"}` for everyone (#214)

The Connect control was `<a href="/api/intervals/auth/init">`, so the browser made a
full-page GET navigation. The SPA keeps the sign-in token in `localStorage` and sends it
only as an `Authorization` header from its fetch wrapper. A navigation does not send that
header, so `require_user()` returned 401 every time (`logs/connect-attempt.log`, section 1).

Fix: init is now `POST /api/intervals/auth/init` (authenticated XHR). It returns
`{"authorize_url": ...}`, and the SPA calls `window.location.assign(authorize_url)`.
The GET route is removed.

### 2. The authorize step fails with `invalid_request` (since 2026-10-02)

`SCOPES` named areas twice: `ACTIVITY:READ,ACTIVITY:WRITE` and
`CALENDAR:READ,CALENDAR:WRITE`. The calendar sync that shipped on 2026-10-02 added the
`CALENDAR` pair, which is why pasting the link broke after that date (ticket #219,
`connect-attempt.log` section 2). `:WRITE` already implies `:READ`, so each area should
appear once.

Fix: `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` in `config.py`. The app
reads wellness and writes calendar and activity data, so the `:READ` entries were
redundant.

Caveat: the logged 400 body is the generic `{"error":"invalid_request"}`, which does not
name the bad parameter. The duplicate-scope cause is the likely one, but I could not
confirm it against the live provider (ground rules: no external calls). Check it by
opening the new `authorize_url` for a test athlete. If it still fails, the next suspect
is `redirect_uri` (see "Not changed" below).

### 3. "Expired, reconnect" about an hour after connecting (#219)

Intervals returns no `refresh_token` and no `expires_in`. The server substituted a
3600 s default, and `refresh_tokens()` then marked every such connection
"expired, reconnect" once it was within 300 s of that fake expiry. It also has no way to
refresh, so the flag was set on a token that was still valid. Rivera's log shows this
exactly: connected 17:41:04, expired 18:37:12 (about 56 minutes, the 55-minute pre-expiry
window plus the 60 s poll).

Fix:
- Removed `DEFAULT_TOKEN_TTL`, `expires_at`, the `refresh_token` field, and the
  `refresh_tokens()` thread.
- Tokens are treated as non-expiring. The token is revoked only when the athlete
  revokes the app.
- Revocation is detected lazily: the first 401 from Intervals on the wellness call runs
  `mark_revoked()`, which clears the token and sets "expired, reconnect". The next status
  check then shows the Connect button again. The SPA does not call `/wellness` yet, so
  until a feature does, a revoked connection still shows as connected. This is expected
  under the lazy design, not a bug.

## Colleague note: what applied

| Note item | Applied? | Notes |
|---|---|---|
| 1. No refresh_token, no expiry; lazy 401 handling; encrypt at rest | **Yes**, except encryption | Expiry and refresh removed; 401 handled lazily. Encryption at rest not added: the store is in-memory (dev), and a real key and storage layer are needed for prod. |
| 2. `Duplicate scope`; each area once | **Yes** | This is the scope fix in cause 2. |
| 3. Token exchange is "standard-lite"; athlete id in response | **Partly** | The athlete id is already read from the token response. The `grant_type` and `redirect_uri` params were left in (see below). |
| 4. Init must be POST, not GET link | **Yes** | This is cause 1. The note's own repro matches the logs. |
| Callback identity via signed `state`, 15-min TTL | **Already present** | `sign_state`/`verify_state` already do this (HMAC, 900 s). Not changed. |
| Add `purpose` claim to `state` | **Not applied** | Only this server signs `state`, so there is no cross-purpose confusion today. Add it if another flow starts signing states with the same secret. |
| Account-mismatch guard on reconnect | **Not applied** | This is a product decision (should a user be able to re-point a connection at a different Intervals athlete?). Add it if the answer is no. |
| Verify steps (wellness, revoke, duplicate scope) | **Applied** locally | See verification below. The live provider was not called. |

Parts of the note that did not apply: the JWT form of `state` (the repo already signs with
HMAC), and the `SETTINGS:WRITE` scope (the app does not use it, so I did not add it).

## Not changed (open items)

- `exchange_code` still sends `grant_type` and `redirect_uri`. The note says the endpoint
  wants only `client_id`, `client_secret` and `code`. The Sept 19 exchange succeeded
  with the current request shape, so I did not change it. If the live authorize step
  still fails, try removing those two fields.
- The token is stored in memory with no encryption. For prod, encrypt it at rest.
- `config.py` still holds placeholder OAuth credentials. The real pair is in the deploy
  environment.
- Rivera (and anyone else connected under the old code) must click Connect once more.
  Their stored connection is `expired, reconnect` and is not revived automatically.

## Verification

I ran the original code and the fixed code against a local mock of the Intervals endpoints
(`INTERVALS_BASE=http://127.0.0.1:9999`). The mock is my assumption of the provider's
behaviour, not the real service; I did not contact intervals.icu.

Original code:
- `GET /api/intervals/auth/init` without a header returns 401, matching the logs.
- The configured scope string is rejected by the mock at authorize (400) because it
  repeats areas.
- After connecting, the token gets a 3600 s expiry, which triggers the refresh-pass
  "expired, reconnect" (matches the Rivera timeline).

Fixed code:
- `GET /api/intervals/auth/init` returns 404 (route removed).
- `POST /api/intervals/auth/init` without a header returns 401; with a Bearer token it
  returns `{"authorize_url": ...}` with a deduplicated scope.
- The authorize step returns 302 (accepted by the mock).
- The callback connects; `/wellness` returns 200 from Intervals.
- After the mock revokes the token, `/wellness` returns 409 and status is
  `expired, reconnect`.
- After a reconnect, `/wellness` returns 200 again.
- `app.js` passes `node --check`, and `server.py`/`config.py` compile.

The one-hour expiry itself was not waited out. It is shown by the removal of the expiry
branch and by the Rivera log timing.

## Changed files

- `config.py`: `SCOPES` deduplicated; `REFRESH_INTERVAL` removed.
- `server.py`: init moved to POST and returns JSON; expiry and refresh removed;
  `mark_revoked()` added; wellness 401 handled.
- `static/app.js`: Connect is a button that POSTs, then navigates to `authorize_url`.
