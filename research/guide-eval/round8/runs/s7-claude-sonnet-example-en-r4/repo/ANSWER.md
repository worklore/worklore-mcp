# Intervals.icu connect: causes and fixes

## Causes
1. **Connect button 401s for everyone.** It was a plain `<a href>` to `GET /api/intervals/auth/init`. A page navigation doesn't send the `Authorization` header the SPA keeps in localStorage, so the server returned `{"error":"unauthorized"}`. Fix: init is now an authenticated `POST` (via the fetch wrapper) that returns `{authorize_url}`. The SPA then calls `window.location.assign()`.
2. **Authorize URL rejected with 400 `invalid_request`.** The calendar sync added `CALENDAR:*` scopes, and `SCOPES` named areas twice (`ACTIVITY:READ,ACTIVITY:WRITE`, `CALENDAR:READ,CALENDAR:WRITE`). Intervals treats `:WRITE` as implying `:READ` and rejects duplicate areas. Fix: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. I did not test this against live Intervals, and the 400 body doesn't name the parameter. The duplicate scope is the only visible defect.
3. **"Expired, reconnect" after an hour.** The Intervals token response has no `refresh_token` or `expires_in`. The code invented a 3600s TTL and a refresher thread that marked the connection expired. The token actually lives until the athlete revokes it. Fix: the TTL and refresher are removed. Revocation is handled lazily: a 401 from Intervals clears the token and sets status "revoked, reconnect".
4. **Token exchange sent extra fields.** It sent `grant_type` and `redirect_uri`. Intervals wants only `client_id`, `client_secret` and `code`. Fix: the exchange now sends only those.

## Colleague's note
- Applied: all four points, which matched the logs. These were the POST init, the no-refresh and no-expiry handling, the no-duplicate-scope rule, and the minimal token exchange. I also added a `purpose` field to the signed `state` and a guard that rejects a reconnect from a different athlete id.
- Not applied: a JWT for `state` (the existing HMAC state with a 15-minute TTL is kept, and I only added the purpose), and encryption at rest (the store is in-memory in this repo; encrypt the token in the prod table).
- Not verified: the live-account check, since I can't reach external services here.

## Also
- `config.py` still has dev placeholder credentials and `APP_SECRET`. Replace them in deploy.
