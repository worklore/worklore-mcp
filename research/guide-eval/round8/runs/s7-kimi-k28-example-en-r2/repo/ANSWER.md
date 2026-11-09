# Intervals.icu integration — causes of the failures and fixes

There were **three independent bugs**, one per reported symptom. All fixes are in
`server.py`, `static/app.js`, and `config.py`.

## Cause 1 — The Connect button 401'd for everyone (ticket #214)

The SPA rendered the Connect action as a plain link:
`<a href="/api/intervals/auth/init">` (`static/app.js`). Clicking it is a
**full-page navigation, which does not carry the `Authorization: Bearer` header** —
the sign-in token lives in `localStorage` and only travels on requests made
through the app's `fetch` wrapper. The backend correctly required auth on
`/api/intervals/auth/init`, so every click ended on `{"error": "unauthorized"}`.
(Rivera's September onboarding only worked because the coach pasted the URL via
`curl`, which did send the header — see `logs/connect-attempt.log` §1–3.)

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that returns
`{"authorize_url"}` as JSON (`server.py`), and the frontend POSTs via its fetch
wrapper and then does `window.location.assign(authorize_url)`
(`static/app.js`). The redirect to Intervals therefore starts from a context
that has the header, and the actual browser navigation to Intervals needs no
auth. The unauthenticated-request guard is unchanged (a bare navigation still
401s, as it should).

## Cause 2 — The authorize step was rejected with 400 since 2026-10-02 (ticket #219)

`config.py` had
`SCOPES = "ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE"`.
Intervals.icu allows **each scope area at most once**: `:WRITE` already implies
`:READ`, and naming an area twice (e.g. `ACTIVITY:READ,ACTIVITY:WRITE`) makes the
authorize endpoint fail with `{"error":"invalid_request"}` ("Duplicate scope")
**before the consent screen**. When the calendar sync shipped on 2026-10-02 it
added `CALENDAR:READ` next to the existing `CALENDAR:WRITE`, duplicating a
second area — that's why even the hand-pasted link stopped working, while the
September flow (scope `ACTIVITY:WRITE,WELLNESS:READ`, per the token-response log)
had gone through.

**Fix:** `config.py` now requests each area once:
`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (write where tricoach writes —
activities, calendar — read-only for wellness).

## Cause 3 — Rivera was told to "reconnect" one hour after a successful connect (ticket #219)

The Intervals.icu token response contains **no `refresh_token` and no
`expires_in`** — the access token lives until the athlete revokes it in the
Intervals UI (confirmed in the captured response in
`logs/connect-attempt.log` §3). The backend nevertheless invented a lifetime:
`store_connection` defaulted `expires_in` to 3600 s, and the background
`refresh_tokens` pass later saw the deadline pass with "no refresh token on
file" and flipped the connection to `expired, reconnect` — about an hour after
connecting, exactly as logged. The token was still valid; the app discarded it
on a false expiry. Rivera hadn't revoked anything.

**Fix:** the connection is stored with **no expiry and no refresh machinery**
(the background refresher thread, `DEFAULT_TOKEN_TTL`, and the
`refresh_token`/`expires_at` fields are gone; `REFRESH_INTERVAL` removed from
`config.py`). Revocation is handled **lazily**: the first **401** from the
Intervals API clears the stored token and marks the user `reconnect`
(`server.py` `disconnect()` / `wellness()`), and the UI asks them to reconnect.
Verified: connected → provider-side revoke → wellness returns 409 and status
flips to `reconnect` → a fresh OAuth round-trip restores the connection.

## Also changed (same provider behavior, per the note)

The token exchange now sends **only** `client_id`, `client_secret`, `code` —
`grant_type` and the `redirect_uri` echo were dropped from `exchange_code()`,
and the `refresh_token` grant path was deleted along with the refresher.
The `state` parameter keeps its HMAC-signed, TTL'd form and gained a `purpose`
marker (`intervals_oauth`) that `verify_state()` now also checks.

## Which parts of the colleague's note applied

Applied as written:

- **"No refresh_token / no expires_in — handle revocation lazily on the first
  401"** → Cause 3. This was the core of the Rivera ticket.
- **"Duplicate scope — each area at most once, `:WRITE` implies `:READ`"** →
  Cause 2. Exact match for the 400 we've seen since the calendar sync shipped.
- **"The init endpoint must be POST returning `{authorize_url}`, frontend does
  `window.location.assign`"** → Cause 1. Exact match for the universal 401
  (full-page navigation drops the auth header).
- **"Token exchange wants only `client_id`, `client_secret`, `code`"** →
  applied as cleanup above; harmless hardening and matches the captured
  provider behavior.
- **"The token response bundles `athlete: {id, name}`"** → already in use; it
  remains how we populate the connection (no "who am I" call needed).

Partially applied / consciously not taken:

- **"`state` as a signed JWT with `sub`/`purpose`/`exp`"** — the substance
  (signature, user binding, 15-minute TTL, purpose check) was already present
  in our HMAC state and is kept; we did not switch its serialization to JWT
  since nothing required it.
- **"Account-mismatch guard on reconnect"** — noted as good practice but not
  part of these failures; left out to keep the change minimal.
- The note's general architecture (SPA with bearer header, same flow shape)
  matched this codebase, which is why its diagnostics mapped 1:1.

## Verification

End-to-end against a local mock of Intervals.icu (via the `INTERVALS_BASE`
override) emulating the documented quirks: duplicate-scope rejection at
authorize, token response with no `refresh_token`/`expires_in`, and 401 after
revocation. 13/13 checks passed: POST init returns the authorize URL; a
headerless navigation still 401s; the fixed scope is accepted while the old
duplicated scope is rejected; authorize → callback → connected as athlete
`i98765`; wellness proxies data; status stays connected (no fake expiry);
revoke → wellness 409 + status `reconnect`; reconnect restores the connection;
and the code exchange sent exactly `client_id`, `client_secret`, `code`.
Mock/test scaffolding was removed after the run.
