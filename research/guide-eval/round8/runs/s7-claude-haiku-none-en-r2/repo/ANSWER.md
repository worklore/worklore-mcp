# Intervals.icu connection: causes

Three things kept athletes from connecting, and one more made a working
connection expire after an hour. Each is listed with its evidence and the fix.

## 1. "Connect" always returns `{"error": "unauthorized"}` (all athletes, #214)

The Connect button was a plain `<a href="/api/intervals/auth/init">`. A plain
navigation does not send the `Authorization: Bearer` header. Only the SPA's
`fetch` wrapper adds it, and the token lives in `localStorage`. So
`require_user()` rejected every click with 401.

The log confirms it: `connect-attempt.log` section 1 shows the document request
with no Authorization header and a 401 body.

**Fix:** `/api/intervals/auth/init` now returns `{"url": ...}` as JSON.
`static/app.js` fetches it through `api()`, which sends the header, and then
sets `location.href` to the URL.

## 2. The authorize step answers 400 `invalid_request` (since 2026-10-02, #219)

The scope string requested both halves of two categories:
`ACTIVITY:READ,ACTIVITY:WRITE,...,CALENDAR:READ,CALENDAR:WRITE`. Intervals.icu
takes one access level per category, and WRITE already implies READ. The 400 is
returned before the consent screen, which is why athletes never see it. It
started with the calendar sync, which added the CALENDAR scopes.

The evidence fits this cause. The body is the same whatever `state` or
`redirect_uri` is (`connect-attempt.log` section 2), so the failing parameter
is one that was not varied, and the scope list is the one that changed.

**Fix:** `config.SCOPES` is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
This grants the same access as before. `ACTIVITY:READ` and `CALENDAR:READ` are
dropped as redundant. The code never reads activities, so `ACTIVITY:WRITE` could
also be removed if that is a product decision.

**Not verified against the live service.** I had no access to Intervals.icu
with real client credentials and did not contact it. The rule about one level
per category comes from public Intervals.icu documentation and is consistent
with the logs. It still needs one real authorize attempt to confirm.

## 3. T. Rivera's connection "expired, reconnect" about an hour after connecting

The 2026-09-19 token response had no `expires_in` and no `refresh_token`
(`connect-attempt.log` section 3). `store_connection()` filled in
`DEFAULT_TOKEN_TTL = 3600`, so the connection was given a one-hour expiry it
never had. When that hour passed, the refresher found no refresh token and
marked the connection `expired, reconnect`, even though the token was still
valid. Rivera's wellness calls had worked until then.

**Fix:** a missing `expires_in` now means "unknown", so no expiry is scheduled.
The connection is marked expired only when Intervals actually answers 401, which
`wellness()` now does. If the token really does die, the athlete finds out on
the next real call, not after an hour.

Caveat: the claim that Intervals tokens have no expiry comes from a third-party
package's documentation, not from Intervals' own docs. The fix does not depend
on it. It only stops the app from inventing an expiry.

## 4. Smaller bugs found while fixing the above

- **Refresher blocked every request.** `refresh_tokens()` held the global `LOCK`
  during each token-endpoint call (up to 15 s each), so every request that
  needed the lock waited. It now copies the due connections under the lock, does
  the network calls without it, and writes results back under the lock.
- **Refresh response without `expires_in` expired the connection.** The code did
  `int(tok["expires_in"])`, which raised `KeyError`, and the connection was then
  marked expired. It now treats the missing value as unknown, as in cause 3.
- **Denied consent looked like a bad request.** `?error=access_denied` showed
  "bad state or code". It now reports "authorization was not granted".
- **Secrets were hard-coded.** `config.py` said the real client pair was in the
  deploy env, but `CLIENT_ID`, `CLIENT_SECRET` and `APP_SECRET` were literals,
  so the deploy env was never read. They now come from `INTERVALS_CLIENT_ID`,
  `INTERVALS_CLIENT_SECRET` and `TRICOACH_APP_SECRET`, with the old values as
  dev defaults. Those variable names are my choice. The deploy env must set
  them, and the existing deploy variable names may differ. If the real secret
  was ever committed or deployed with the dev default, rotate it.

## Verification

- `flow_test.py` starts `server.py` on port 8790 against a local mock of
  Intervals.icu. The mock rejects duplicate scope categories and issues tokens
  with no `expires_in` or `refresh_token`, as in the 09-19 log. All 10 checks
  pass: connect with and without the Bearer header, authorize with the new scope
  set, callback, status, wellness, expiry on an Intervals 401, and reconnect.
- One refresher pass was run with `post_form` stubbed. It covered a successful
  refresh, a missing refresh token, a failing refresh, and a token with no
  expiry.
- Not tested against the real Intervals.icu. That needs the real client
  credentials, and the authorize step is the one that matters.

## Still to do (outside this repo)

- A `server.py` is running on port 8766 (PID 9025, started 12:23 AM). It was not
  started by me and I did not stop it. It is still running the old code, so
  restart it to pick up these changes.
- Set `INTERVALS_CLIENT_ID`, `INTERVALS_CLIENT_SECRET` and `TRICOACH_APP_SECRET`
  in the deploy environment.
- Run one real Connect against Intervals.icu once the credentials are in place.
