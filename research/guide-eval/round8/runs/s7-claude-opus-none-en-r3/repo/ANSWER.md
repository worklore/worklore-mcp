# Intervals.icu connection: causes and fixes

There were three separate faults. Any one of them on its own would stop athletes from staying connected.

## 1. The Connect button can never authenticate (ticket #214, log §1)
The tricoach sign-in token lives in `localStorage` and is only sent as
`Authorization: Bearer …` by the SPA's `fetch` wrapper. The button was a plain
`<a href="/api/intervals/auth/init">`, so clicking it is a normal browser page load
with no Authorization header. `auth_init` therefore returns `401 {"error": "unauthorized"}`
for every athlete. The log shows this: "401 (no Authorization header)", document
navigation, `Accept: text/html`.

**Fix:** the button now calls `/api/intervals/auth/init` through `api()` with
`Accept: application/json`. The server returns `{"authorize_url": …}` and the SPA
navigates there itself. Requests without JSON in `Accept` still get the 302, so the
curl workflow keeps working. The callback was already fine without the header,
because it identifies the user from the signed `state`.

## 2. The authorize request is rejected with `invalid_request` (log §2)
When calendar sync shipped on 2026-10-02, the scope list became
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
Intervals.icu expects one entry per area, either `:READ` or `:WRITE`, where WRITE
already includes READ. Asking for both levels of the same area makes the authorize
step fail before the consent screen. The connection that worked before that date
asked for `ACTIVITY:WRITE,WELLNESS:READ` (the scope echoed in Rivera's token response).
That fits the same one-entry-per-area format.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"` in `config.py`.
This still gives the activity and calendar read access the app needs.

## 3. Working connections were thrown away after an hour (ticket #219, log §3)
Intervals.icu issues long-lived access tokens. They stay valid until the athlete
revokes the app, and the token response has no `refresh_token` or `expires_in`
(see Rivera's response). `store_connection` filled the missing `expires_in` with a
made-up `DEFAULT_TOKEN_TTL = 3600`. About 55 minutes later the refresher found no
refresh token and set the connection to "expired, reconnect", deleting a token
that was still valid. Rivera never revoked anything.

**Fix:** if the provider sends no `expires_in`, the connection is stored with
`expires_at = None` and the refresher skips it. If a provider does send
`expires_in`/`refresh_token`, the refresh path still handles it. The only real way
these tokens die is the athlete revoking the app. That is now detected when
Intervals answers a wellness call with 401, and only then is the connection marked
"expired, reconnect".

## Notes
- Rivera's stored token was erased (`access_token=None`) when the connection was
  wrongly expired, so it can't be recovered. They need to click Connect once more
  now that the button works.
- Checked locally against a stub Intervals server: the button fetches the authorize
  URL (200 JSON), the callback exchanges the code (302 to `/?connected=1`), the
  status shows connected with a "non-expiring token", and the wellness proxy
  returns 200. The fixed scope string was not tested against the real
  intervals.icu, per the ground rules.
