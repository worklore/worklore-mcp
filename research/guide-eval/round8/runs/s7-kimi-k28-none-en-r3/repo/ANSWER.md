# Why the Intervals.icu connection was failing

Three independent defects, matching the three reported symptoms.

## 1. The Connect button 401'd for every athlete

**Cause:** the SPA rendered "Connect Intervals.icu" as a plain link
(`<a href="/api/intervals/auth/init">` in `static/app.js`). Clicking it is a
browser document navigation, and browsers cannot attach a custom
`Authorization` header to a navigation. The dev sign-in token lives in
`localStorage` and is only added by the SPA's `fetch` wrapper — so the request
reached `auth_init` with no credentials and `require_user()` answered 401.
Confirmed in `logs/connect-attempt.log` §1: the failing request is a document
navigation with no Authorization header.

**Fix:** `/api/intervals/auth/init` now returns the authorize URL as JSON
(`{"authorize_url": ...}`) and the SPA's Connect button obtains it via
`api()` — which sends the Bearer header — and then navigates
(`static/app.js`, `server.py` `auth_init`). Also added the spec-required
`response_type=code` to the authorize URL.

## 2. The authorize step returned `400 invalid_request` (since 2026-10-02)

**Cause:** the scope list asked for **both** READ and WRITE for the same
scope: `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Per the Intervals.icu OAuth docs, each scope must be specified once — READ
**or** WRITE, where WRITE implies READ — and the provider rejects a list that
specifies both variants. The September flow worked because its granted scopes
were `ACTIVITY:WRITE,WELLNESS:READ` (one variant per scope, per
`logs/connect-attempt.log` §3); the calendar-sync release on 2026-10-02
rewrote `SCOPES` with duplicated `:READ`/`:WRITE` pairs, which is exactly when
the consent screen stopped appearing (`logs/connect-attempt.log` §2,
`logs/support-tickets.md` #219). The support notes about removing `state` or
changing `redirect_uri` changed nothing because the offending parameter was
`scope`.

**Fix:** `config.py` `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`
— one variant per scope; WRITE covers the read side per the docs.

## 3. Connections wrongly showed "expired, reconnect" after about an hour

**Cause:** Intervals.icu token responses contain **no `refresh_token` and no
`expires_in`** (see the captured response in `logs/connect-attempt.log` §3 and
the provider docs). Their access tokens do not expire on their own; a token
only dies when the athlete revokes the app, which then shows up as HTTP 401
on API calls. The server invented a one-hour TTL
(`DEFAULT_TOKEN_TTL = 3600` when `expires_in` is absent), and the background
refresher declared the connection dead as soon as that fabricated deadline
passed with no refresh token — hence Rivera's connection dying ~56 minutes
after the onboarding call despite nothing being revoked (tricoach was still
listed under their Intervals apps).

**Fix:** a missing `expires_in` now means the token does not expire
(`expires_at = None`); the refresher leaves non-expiring connections alone
and only gives up on a connection when the provider definitively refuses a
refresh (4xx). A 401 from the Intervals API (e.g. in `wellness()`) marks the
connection "expired, reconnect", so athletes are only asked to reconnect when
the token actually stopped working.

## Verification

End-to-end against a local mock of the documented Intervals.icu API (via the
`INTERVALS_BASE` override; no external service contacted): Connect flow
completes (`auth/init` → authorize 302 → callback → `/?connected=1`), status
shows connected, wellness proxies data, the connection survives past the old
one-hour mark, a revoked token (API 401) flips status to "expired, reconnect",
and a full disconnect/reconnect cycle works. The old duplicated scope string
is rejected (400) by the same provider-side scope validation while the fixed
one is accepted.
