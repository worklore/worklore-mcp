# Intervals.icu connection: causes and fixes

Three separate bugs. Each one alone is enough to block athletes.

## 1. The Connect button can never authenticate (ticket #214, log §1)

The button was a plain `<a href="/api/intervals/auth/init">`. That makes the
browser load a new page, and a page load does **not** send the
`Authorization: Bearer …` header. The SPA only adds that header in its
`fetch` wrapper (the token is kept in `localStorage`). So `auth_init` never saw
a user and returned `401 {"error":"unauthorized"}` to every athlete, on every
browser.

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that
returns `{"authorize_url": …}` as JSON. The button calls it through `api()`,
so the header is sent, and then runs `window.location.assign(authorize_url)`.
The callback still finds the user through the signed `state` parameter. It
has to, because the redirect back from Intervals carries no auth header
either. (`server.py` `auth_init` and routing, `static/app.js`.)

## 2. Intervals rejects the scope list: "Duplicate scope" (log §2)

The calendar-sync release on 2026-10-02 changed `SCOPES` to
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
On Intervals.icu, `:WRITE` already includes `:READ`, and each area may be
listed only once. Naming an area twice gets the request rejected at
`/oauth/authorize` with `400 invalid_request` before the consent screen
appears. That is why pasting the link by hand stopped working too. Look at
Rivera's earlier grant: it came back as `ACTIVITY:WRITE,WELLNESS:READ`, one
entry per area.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` in
`config.py`. It still covers reading and writing for activities and the
calendar.

## 3. Working connections were marked expired after 1 hour (ticket #219, log §3)

Intervals.icu access tokens do not expire. The token response has no
`expires_in` and no `refresh_token`, and the token stays valid until the
athlete revokes the app. `store_connection` filled in a made-up
`DEFAULT_TOKEN_TTL = 3600`. An hour later the refresher found no refresh
token, marked the connection `expired, reconnect` and threw away a token that
still worked. Rivera never revoked anything; the app gave up on its own.

**Fix:** if there is no `expires_in`, `expires_at` is stored as `None` and the
refresher skips it. Renewal only happens if the provider actually sends an
expiry. Since tokens never expire, the way to notice a revoked token is now
lazy: a 401 from the Intervals API (in `/wellness`) marks the connection
`expired, reconnect` and shows the reconnect prompt.

Note: Rivera's stored token was already wiped (`access_token=None`), so
Rivera has to click Connect **once** more. After that the connection stays
up.

## Verification

I ran the server against a local fake Intervals server
(`INTERVALS_BASE=http://127.0.0.1:8799`). The old GET link no longer exists,
and `POST /auth/init` with the bearer token returns the authorize URL with
the fixed scope. The callback stores the token as "no expiry", and `status`
and `wellness` both return 200. I did not test against the real
intervals.icu.

## Not fixed, worth a look

- OAuth client secrets are committed in plain text: the dev secret is
  hard-coded in `config.py`, and the README has the **staging** secret in it.
  They should be moved to environment variables and rotated.
- Intervals tokens never expire, so they are permanent credentials. In prod
  they should be encrypted at rest.
