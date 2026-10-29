# Intervals.icu connection: causes and fixes

## Causes

1. **Connect button always returns 401 (`unauthorized`).** The button was a plain
   `<a href="/api/intervals/auth/init">`. A link navigation does not send the
   `Authorization: Bearer` header the SPA uses, so `require_user()` rejects it. This
   is why nobody gets past the button (ticket #214, log section 1).

2. **Authorize step returns `400 invalid_request` before the consent screen.** Two
   candidates, neither confirmed against Intervals:
   - The authorize URL had no `response_type=code`, which OAuth2 requires (RFC 6749
     §4.1.1). This is a spec violation and is fixed.
   - The scope list includes `CALENDAR:READ,CALENDAR:WRITE`. The ticket says the 400
     started when calendar sync shipped on 2026-10-02, and Rivera's connection from
     before that date (wellness/activity scopes only) worked. This points at the
     calendar scopes, most likely because the Intervals client is not registered for
     them. I could not check the Intervals side from here.

   The 400 body does not name the bad parameter (ticket #219 notes this), which fits
   either candidate.

3. **Athletes are marked "expired, reconnect" about an hour after connecting.** The
   token response had no `expires_in` and no `refresh_token` (log section 3). The code
   substituted a guessed lifetime of `DEFAULT_TOKEN_TTL = 3600` s, and the background
   refresher then expired the connection when that guess ran out. The real lifetime
   was never known. The "about an hour" is our assumption, not the provider's.

4. **A revoked or rejected token still showed "connected".** A 401 from Intervals on a
   wellness call was passed through to the client, but the stored status stayed
   `connected`, so the card never offered a reconnect.

5. **Client credentials were never read from the deploy env.** `config.py` says the
   real OAuth client pair is in the deploy env, but nothing read it. Every deploy used
   the dev placeholders `tricoach-dev` / `s3cr3t-placeholder-0000`.

## Fixes

- `server.py`: `/api/intervals/auth/init` now returns `{"url": ...}` as JSON, and
  `response_type=code` is added to the authorize URL.
- `static/app.js`: Connect is a button. It calls `auth/init` with the Bearer token and
  then navigates to the returned URL.
- `server.py`: no lifetime is invented. With no `expires_in`, `expires_at` is `None`,
  the refresher skips the connection, and the token is used until Intervals rejects it.
  A token with a known expiry and no refresh token still expires at that time.
- `server.py`: a 401 from Intervals on a wellness call marks the connection
  `expired, reconnect` and clears the access token, so status shows it and the athlete
  can reconnect.
- `config.py`: `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET`, `APP_SECRET` and
  `INTERVALS_SCOPES` are read from the environment, with the dev values as fallbacks.

## Verification

Ran `server.py` against a local fake Intervals (not committed; it only mimicked the
behaviour in the logs):

- No `Authorization` header on `auth/init` gives 401. With the header it gives 200 and
  a URL containing `response_type=code`.
- With the default scopes (`CALENDAR:*` included), the fake returns 400, reproducing
  ticket #219.
- With `INTERVALS_SCOPES=ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ`, the flow completes:
  authorize, callback 302 to `/?connected=1`, status `connected`, wellness 200.
- A token with no expiry on file is still `connected` after a refresher pass (62 s).
- After the token is revoked at the fake, wellness returns 409 and status becomes
  `expired, reconnect`.

`app.js` passes `node --check`, and both Python files compile. I did not test against
the real Intervals.icu, and I did not deploy anything.

## Still open (needs a person with Intervals access)

- **Scopes.** Check which scopes the Intervals OAuth client is registered for. If
  `CALENDAR:*` is not granted, either register it or set `INTERVALS_SCOPES` without
  calendar scopes. Calendar sync needs them, so this is a product decision as well as a
  config one. Until this is settled, Connect can still fail on the default scopes.
- **Deploy env.** Set `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET` and `APP_SECRET`
  in the deploy environment. The fallback `APP_SECRET` is a dev value in the repo.
- **Athletes to reconnect.** Connections are in memory, so a restart clears them. Each
  athlete, Rivera included, has to click Connect again once the scope question is
  settled. The token lifetime is still unknown. The new `expires_in=` line in the log
  on the next real connection will show whether Intervals returns one.

## Not changed

- The refresher holds `LOCK` during its HTTP calls, so a slow token refresh (up to 15 s
  per user) blocks status and wellness requests. This is not part of the reported
  failures, so I left it alone.
