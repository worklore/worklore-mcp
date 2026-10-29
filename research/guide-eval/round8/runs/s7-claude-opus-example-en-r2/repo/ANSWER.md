# Intervals.icu connection — causes and fix

Three separate bugs. Each one would have been enough to break things on its own.

## 1. The Connect button can never authenticate (ticket #214, everyone)

`static/app.js` rendered Connect as `<a href="/api/intervals/auth/init">`, and
`auth_init` was a `GET` that required `Authorization: Bearer …`. Our sign-in
token is kept in `localStorage` and only the fetch wrapper adds it. A page
navigation doesn't send that header, so every click ended in
`401 {"error": "unauthorized"}`. `logs/connect-attempt.log` §1 shows this: a
document navigation with no Authorization header.

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that returns
`{"authorize_url": …}`. The button calls it with `api(…, {method: "POST"})` and
then runs `window.location.assign(authorize_url)`. The old GET route is gone.

## 2. Intervals rejects the authorize URL: duplicate scope areas (since the 2026-10-02 calendar sync)

`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
In Intervals, `AREA:WRITE` already includes `AREA:READ`, and naming the same area
twice gets the request rejected. That matches log §2: a 400 with no consent
screen, and the same 400 when `state` or `redirect_uri` is changed, so neither
of those is the cause. The error body we capture is a generic
`{"error":"invalid_request"}`, not the literal "Duplicate scope" text. Rivera's
grant on 2026-09-19 came back as `ACTIVITY:WRITE,WELLNESS:READ`, with no
duplicated area and no calendar, and that one worked.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`, so each area
appears once. That still covers everything the app does: it reads wellness and
writes calendar and activity.

## 3. Working connections were thrown away after an hour (ticket #219, Rivera)

Intervals tokens have no `expires_in` and no `refresh_token`. They stay valid
until the athlete revokes the app. `store_connection` filled in a made-up
`DEFAULT_TOKEN_TTL = 3600`. The background `refresh_tokens` thread then found
no refresh token, nulled the access token and set `expired, reconnect`. That is
the log line at 18:37:12, about an hour after Rivera connected. Rivera never
revoked anything.

**Fix:** removed the fake TTL, the `expires_at` / `refresh_token` fields and
the refresher thread. Revocation is now detected lazily. A 401 from the
Intervals API (in `/api/intervals/wellness`) clears the token and sets the
status to `revoked, reconnect`, and the SPA shows the Connect button again.
Rivera's stored token was already nulled, so Rivera has to reconnect once.
After that the connection stays up.

Small extra: if the athlete declines on the consent screen, the callback now
redirects to `/?intervals_error=…` instead of replying with "bad state or code".

## Verification

I ran the patched server on port 8767 against a local mock of Intervals
(`INTERVALS_BASE`; no real Intervals calls). Port 8766 already had a server on
it that I didn't start (PID 9025), so I left it alone. Results:

- GET init returns 404, POST without auth returns 401, and POST with auth
  returns `authorize_url` with the new scope.
- Authorize, callback and token exchange end in `302 /?connected=1`. Status
  shows connected and wellness returns data.
- After a mock revocation, wellness returns 401 from Intervals, which becomes
  status `revoked, reconnect` instead of a crash.

The mock only covers the behaviour described above. I haven't tested the new
scope string against real Intervals, so please do one real connect on dev
before telling athletes it's fixed.

## Which parts of the colleague's note applied

- **Applied, #4 (init must be POST + JSON `authorize_url`):** this is cause 1,
  and it's fixed the way the note describes.
- **Applied, #2 (Duplicate scope):** this is cause 2. Our scope list is
  different from theirs. We don't use `SETTINGS:WRITE`, so I didn't copy their
  list.
- **Applied, #1 (no refresh_token / no expiry, handle 401 lazily):** this is
  cause 3.
- **Not applied, #3 (send only `client_id`, `client_secret`, `code` to the
  token endpoint):** our exchange also sends `grant_type` and `redirect_uri`,
  and Rivera's exchange still succeeded with them (log §3). It isn't a cause
  here, so I left it unchanged. The `athlete {id, name}` in the response was
  already being used.
- **Not needed, JWT `state`:** our HMAC-signed `user_id:timestamp` state with a
  15-minute max age already does the same job (signed identity plus TTL). I
  kept it.
- **Not done (worth doing, not a cause):** encrypting tokens at rest in prod
  (this repo keeps them in memory), and an account-mismatch guard on reconnect.
- **Ignored:** the forum link for client registration and the "Reproduce"
  steps against a live account. The ground rules for this task don't allow
  contacting external services.
