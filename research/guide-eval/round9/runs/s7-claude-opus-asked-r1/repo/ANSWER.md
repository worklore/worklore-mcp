# Intervals.icu connection: causes and fixes

There are three separate bugs. The first two each stop anyone from connecting. The third one disconnected the one athlete who did get through.

## 1. Connect button gives 401 for everyone (ticket #214)

The button was a plain `<a href="/api/intervals/auth/init">`, so clicking it loaded a new page. The sign-in token is in `localStorage`, and only the SPA's `fetch` wrapper sends it as `Authorization: Bearer`. A normal page load doesn't send that header, so `auth_init` saw no user and returned `{"error": "unauthorized"}` (log §1: a page request with no Authorization header).

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST**. It returns `{"authorize_url": ...}` as JSON. The button calls it with `fetch` and then runs `window.location.assign(authorize_url)` (`server.py` `do_POST`/`auth_init`, `static/app.js`). The callback still finds the user from the signed `state` parameter, because Intervals' redirect back carries no auth header either.

## 2. Authorize step returns `invalid_request` (log §2)

The calendar sync shipped on 2026-10-02 and changed the scope to `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. Intervals.icu lets you name each area **only once**, and `:WRITE` already includes `:READ`. Naming an area twice is rejected as "Duplicate scope", which shows up here as a bare `invalid_request` before the consent screen. Rivera's grant from before the change was `ACTIVITY:WRITE,WELLNESS:READ`, which names each area once.

**Fix:** `config.SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`.

## 3. "Expired, reconnect" an hour after connecting (ticket #219, log §3)

Intervals.icu tokens come with no `expires_in` and no `refresh_token`. They stay valid until the athlete revokes the app. `store_connection` filled in a made-up `DEFAULT_TOKEN_TTL = 3600`. An hour later the refresher found no refresh token and marked the connection "expired, reconnect", even though the token was still valid and Rivera never revoked anything.

**Fix:** the made-up TTL is gone. A connection only gets an expiry if Intervals actually sends `expires_in`, and the refresher skips connections with no expiry. Revocation is now caught when it happens: if the API answers 401, the connection is marked "expired, reconnect" and the stored token is cleared.

## Verification

I ran the server against a local stub of Intervals' endpoints, not the real Intervals.icu:
- `GET /auth/init` → 404, and an authenticated `POST` → 200 with the authorize URL and the corrected scope.
- The callback exchanges the code and redirects to `/?connected=1`. The log says "no expiry".
- Wellness → 200. After the stub starts answering 401 ("revoked"), wellness → 409 and status → `expired, reconnect`.

Not tested: a real consent and token exchange against intervals.icu with the dev client. That needs a real athlete account.

## Other things found (not changed)
- Secrets are committed in plain text: the dev client secret is the fallback in `config.py`, a staging client secret is in `README.md`, and `APP_SECRET` is hardcoded. Rotate them and load them from the environment.
- Tokens never expire, so they should be encrypted at rest in the prod table.
- `refresh_tokens` makes network calls while holding `LOCK`.
