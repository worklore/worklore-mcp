# Why athletes couldn't connect Intervals.icu — causes and fixes

Three independent defects, one per reported symptom. All fixed in `server.py` and
`static/app.js`; verified end-to-end (16/16 checks) against a local mock of the
Intervals.icu endpoints — no external service was contacted.

---

## Cause 1 — The Connect button sends no credentials → 401 for everyone

**Symptom:** every athlete clicking "Connect Intervals.icu" lands on a white page
showing `{"error": "unauthorized"}` (ticket #214, log §1).

**Cause:** the sign-in token lives in `localStorage` and is only ever attached to
requests by the SPA's fetch wrapper (`Authorization: Bearer …` in `api()`). The
Connect control was a plain link — `<a href="/api/intervals/auth/init">` — i.e. a
browser document navigation, which cannot carry a custom `Authorization` header.
`/api/intervals/auth/init` requires that header, so the server answered 401. The
browser dev-tools capture in the log shows exactly that: an `Accept: text/html…`
navigation request with no `Authorization` header.

**Fix:** `/api/intervals/auth/init` now returns `{"url": "<authorize url>"}` as JSON,
and the SPA's Connect button calls it through the `api()` fetch wrapper (token
attached) and then navigates the browser to the returned URL
(`server.py` `auth_init`, `static/app.js` connect handler). A bare navigation
without the header still 401s, as it should.

## Cause 2 — The authorize URL was missing `response_type=code` → `invalid_request`

**Symptom:** since 2026-10-02, even a hand-pasted authorize link dies at
intervals.icu with HTTP 400 `{"error":"invalid_request"}` before any consent
screen (log §2, ticket #219).

**Cause:** the authorize URL built in `auth_init` contained `client_id`,
`redirect_uri`, `scope` and `state` but **not the required `response_type=code`
parameter** (RFC 6749 §4.1.1). Intervals.icu rejects the request as
`invalid_request`. The log's own observation pins this down: dropping `state` or
changing `redirect_uri` produced the same error, so neither of those was the
parameter the provider minded. The new calendar scopes were a red herring —
`CALENDAR:READ`/`CALENDAR:WRITE` are valid Intervals.icu scopes; the authorize
URL just happened to be edited in the same 2026-10-02 "calendar sync" change that
dropped `response_type`.

**Fix:** `response_type=code` added to the authorize parameters (`server.py`
`auth_init`). A mock provider enforcing RFC-required parameters 400s without it
and consents with it (verified).

## Cause 3 — The server invents a 1-hour expiry for tokens that never expire

**Symptom:** the one athlete who connected (T. Rivera, 2026-09-19) was told
"Status: expired, reconnect" about an hour later, and reconnecting was impossible
because of causes 1–2 (log §3, ticket #219).

**Cause:** Intervals.icu departs from typical OAuth providers — **its access
tokens do not expire and it never issues refresh tokens**, so its token response
contains no `expires_in` and no `refresh_token` (exactly what Rivera's logged
token response shows). `store_connection` substituted a made-up
`DEFAULT_TOKEN_TTL = 3600` when `expires_in` was absent, and the background
refresher then marked the connection "expired, reconnect" after that hour — with
no refresh token available to recover. The expiry was entirely our own fabrication.

**Fix:** no `expires_in` in the token response is now stored as a non-expiring
token (`expires_at = None`); the refresher skips non-expiring tokens instead of
expiring them (logic extracted to `refresh_pass()`). If Intervals.icu ever
rejects a stored token (401), the connection is marked "expired, reconnect" and
the athlete is sent through the flow again — that recovery path now also works,
since causes 1 and 2 are fixed. The refresh-token code path is retained for
providers/tokens that do carry `expires_in`/`refresh_token` (verified against the
mock: expiring token + refresh token → renewed; expiring token without refresh
token → "expired, reconnect").

---

## Verification

A local mock of `intervals.icu` (authorize / token / wellness) was run together
with the app via the `INTERVALS_BASE` override; 16/16 checks passed, covering:
401 without the Bearer header, 200 + valid authorize URL with it, the provider
400 on missing `response_type`, the full authorize→callback→connected flow,
wellness proxying, no expiry after a simulated 2 h, refresh of expiring tokens,
honest expiry without refresh tokens, 401→reconnect marking, and reconnecting
afterwards. The throwaway test script was removed after the run; `python3 -m
py_compile server.py config.py` and `node --check static/app.js` are clean.

## References

- Intervals.icu API guide & rate limits — [forum.intervals.icu/t/609](https://forum.intervals.icu/t/api-access-to-intervals-icu/609)
- Intervals.icu OAuth scopes are comma-joined; "Tokens do not expire, and there are no refresh tokens" — [ueberauth_intervals_icu](https://libraries.io/hex/ueberauth_intervals_icu)
- Working OAuth2 flow example for Intervals.icu (`response_type=code`, comma/space scope variants) — [@kuranov/intervals-client](https://github.com/kuranov/intervals-icu-tools)
- RFC 6749 §4.1.1 (`response_type` required on authorize) — [tools.ietf.org/rfc/rfc6749](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1.1)

## Notes / not the cause

- The calendar scopes (`CALENDAR:READ,CALENDAR:WRITE`) are valid; keep them.
- Redirect URIs must be registered in full at intervals.icu (no wildcards) — the
  2026-09-19 flow proves `http://localhost:8766/api/intervals/callback` is
  already registered for the dev client.
- The default `Python-urllib` user agent may be challenged by Cloudflare; not
  implicated in these failures (the September token exchange used it fine), so it
  was left untouched.
