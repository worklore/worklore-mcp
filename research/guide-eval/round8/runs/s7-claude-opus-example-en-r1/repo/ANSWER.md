# Intervals.icu connection: causes and fixes

There were three separate faults. Any one of them was enough to stop athletes from connecting.

## 1. Every click on Connect gave 401: the init endpoint was a GET link

`static/app.js` drew Connect as `<a href="/api/intervals/auth/init">`, and
`auth_init` called `require_user()`. Clicking a link loads a whole new page. The browser
does not send the `Authorization: Bearer` header on that request, because only
the SPA's `fetch` wrapper sends it. So the request always came in without
credentials and got 401 `{"error": "unauthorized"}`. This matches log §1
("no Authorization header", Accept: text/html, document navigation) and ticket #214.

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that
returns `{"authorize_url": ...}` as JSON. The Connect button calls it through
`api()` and then does `window.location.assign(authorize_url)`. A GET to that
path now returns 404.

## 2. Pasting the authorize link gave 400 `invalid_request`: duplicate scope areas

`config.SCOPES` was
`ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`.
On Intervals, `:WRITE` already includes `:READ`, and naming the same area twice
is rejected. Here both ACTIVITY and CALENDAR were named twice.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. This asks
for the same access as before.

How sure is this? The response body does not name the bad parameter, and it
does not say "Duplicate scope" the way the colleague's note describes. It is
just `invalid_request`. The diagnosis rests on three things:
- The ticket says the failures started when calendar sync shipped on 2026-10-02 and added calendar scopes.
- Rivera's working September grant was `ACTIVITY:WRITE,WELLNESS:READ`, with each area named once.
- The log says changing `state` or `redirect_uri` gives the same error, so those are not the cause.

Confirm it with one real authorize request using the new scope string before
telling athletes it's fixed.

## 3. A working connection was marked "expired, reconnect" after about an hour: a made-up expiry

Intervals tokens include no `expires_in` and no `refresh_token`. They stay valid
until the athlete revokes the app. `store_connection` filled in
`DEFAULT_TOKEN_TTL = 3600` anyway. About an hour later, the background refresher
found no refresh token and marked Rivera's connection
`expired, reconnect`, even though the token was still valid. That is log §3
and ticket #219: Rivera never revoked anything, and tricoach is still listed in their Intervals apps.

**Fix:**
- No expiry is stored when the provider sends none (`expires_at = None`), and the refresher skips those connections.
- Revocation is now detected when it actually happens: if the wellness proxy gets a 401 from Intervals, it clears the token and sets the status to `revoked, reconnect`.

Rivera's stored token was already thrown away, so Rivera has to connect once more after this deploy.

## Verification

I ran the patched server against a local fake Intervals. The fake rejects
duplicate scope areas with 400 `invalid_request`, and its token response has no
expiry or refresh token. Results:
- GET init returns 404; POST init returns `authorize_url` with the new scope string.
- Authorize redirects to the callback, the callback exchanges the code, and the connection is logged as "no expiry; valid until revoked".
- `/wellness` returns 200.
- After the fake revokes the token, `/wellness` handles the 401 and status becomes `revoked, reconnect`.

This was not tested against the real intervals.icu.

## Which parts of the colleague's note applied

- **Quirk 1 (no refresh_token, never expires; handle revocation lazily on 401): applied.** This is cause 3. I did **not** add encryption at rest: storage here is an in-memory stand-in. The note's advice is still worth following for the prod Postgres table.
- **Quirk 2 (Duplicate scope): applied.** This is cause 2, although Intervals answered with `invalid_request` rather than the "Duplicate scope" message the note quotes. I left out the note's `SETTINGS:WRITE`, because this app doesn't need it.
- **Quirk 3 (token exchange needs only client_id/secret/code): not applied.** Our exchange also sends `grant_type` and `redirect_uri`, and Rivera's exchange succeeded with exactly that request, so Intervals tolerates the extra fields. It was not a cause, so I left it unchanged. The note's point that the response includes `athlete.id` was already being used.
- **Quirk 4 (init must be an authenticated POST returning `{authorize_url}`): applied.** This is cause 1, with the same fix.
- **State carries identity, signed, 15-minute TTL: already in place.** `sign_state`/`verify_state` use HMAC with `max_age=900`. I did not switch to a JWT or add a `purpose` claim, since that would change nothing that's broken.
- **Account-mismatch guard on reconnect: not applied.** It's a reasonable safeguard to add later, but it had nothing to do with these failures.
- **The "Reproduce this" steps (registering a client, real-account verification, revoking in the Intervals UI): not applicable here.** I only work locally and don't contact external services. Those steps are what to run in staging with the real client credentials.
