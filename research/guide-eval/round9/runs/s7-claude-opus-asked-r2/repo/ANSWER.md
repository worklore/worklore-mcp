# Intervals.icu connection: causes and fixes

## 1. The Connect button can never authenticate (ticket #214, everyone)

`static/app.js` rendered Connect as a plain link, `<a href="/api/intervals/auth/init">`,
and `auth_init` in `server.py` was a GET that called `require_user()`. The SPA keeps the
sign-in token in `localStorage` and sends it as `Authorization: Bearer` only from its
`fetch` wrapper. Clicking a link loads a new page, and the browser sends no
`Authorization` header with it. So every click reached `/auth/init` without the header and
got `401 {"error": "unauthorized"}`. That matches `connect-attempt.log` §1: a document
navigation whose request headers show only `Accept`/`Referer`, logged as
"401 (no Authorization header)".

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that returns
`{"authorize_url": ...}` as JSON. The Connect button calls it through `api()`, so the
header is sent, then calls `window.location.assign(authorize_url)`. The callback still
works out which user it belongs to from the signed `state` parameter, because the
redirect back from Intervals carries no auth header either.

## 2. Intervals rejects the authorize request because of the scope string (pasted link, since 2026-10-02)

When calendar sync shipped, `config.SCOPES` became
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals allows each area (ACTIVITY, WELLNESS, CALENDAR, …) to appear only once in the
scope list, and `:WRITE` already includes `:READ`. Naming an area twice gets a
"Duplicate scope" rejection. Here it shows up as a bare `400 {"error":"invalid_request"}`
before any consent screen (log §2), and removing `state` or changing `redirect_uri` didn't
change it, which rules those two out. Rivera's working connection in September was
granted exactly `ACTIVITY:WRITE,WELLNESS:READ`, with one entry per area.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. This still covers
reading activities and calendar, writing planned workouts, and reading wellness.

## 3. Working connections were expired after an hour (ticket #219)

Intervals.icu access tokens have no `expires_in` and no `refresh_token`. They stay valid
until the athlete revokes the app in Intervals (log §3 shows the token response: neither
field is there). `store_connection` assumed a 3600 s lifetime when `expires_in` was
missing (`DEFAULT_TOKEN_TTL`). The background refresher then found an "expiring" token
with nothing to refresh it with and set it to `expired, reconnect`. That is about an hour
after Rivera connected, while their token was still valid and tricoach was still listed
in their Intervals apps.

**Fix:** if the provider doesn't send `expires_in`, the connection gets no expiry
(`expires_at = None`) and the refresher skips it. A revoked token is now detected when it
fails: a 401 from the Intervals API marks the connection `expired, reconnect`, and the
user is asked to reconnect.

## Verification

Tested locally against a mock of Intervals that rejects repeated scope areas and returns
tokens like the real one (no `expires_in`/`refresh_token`): POST init → authorize →
callback → connected with "no expiry" → wellness 200 → after revocation, wellness gets
401 → status `expired, reconnect`. GET init now returns 404. I have not tested against
the real intervals.icu.

## Follow-ups

- Prod connections already set to `expired, reconnect` by the 1-hour timer (e.g. Rivera)
  still hold their token in the DB only if it wasn't cleared. The old code set
  `access_token=None`, so those athletes need to reconnect once with the fixed button.
- Secrets are in the repo: `config.py` has a client secret as a hard-coded fallback, and
  `README.md` has a staging client secret in plain text. Rotate them and move them to the
  environment. Intervals tokens never expire, so they should also be encrypted at rest in
  prod.
