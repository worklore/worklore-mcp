# Intervals.icu connection: why it failed and what changed

Three separate bugs, one per symptom. Each one alone breaks the flow.

## 1. "Connect" returns `{"error": "unauthorized"}` for everyone (ticket #214)

**Cause.** The button was `<a href="/api/intervals/auth/init">`, a GET that is
a full-page navigation. The browser does not send the `Authorization: Bearer`
header on navigation. The SPA keeps the token in `localStorage` and attaches it
only in the `fetch` wrapper, so `require_user()` got no header and returned 401
(`logs/connect-attempt.log`, section 1).

**Fix.** `auth/init` is now `POST` and returns `{"authorize_url": ...}` as JSON.
The button calls it through `api()` (which sends the header) and then does
`window.location.assign(authorize_url)`.

## 2. Authorize step fails with 400 once calendar sync shipped (2026-10-02)

**Cause.** `SCOPES` listed `ACTIVITY:READ` next to `ACTIVITY:WRITE`, and
`CALENDAR:READ` next to `CALENDAR:WRITE`. `:WRITE` already implies `:READ`, so
each pair names the same area twice. Intervals rejects that with
`Duplicate scope`. The calendar change added the second pair, which matches the
timing in ticket #219. Pasting the link by hand also fails
(`logs/connect-attempt.log`, section 2). This is also why the "pasted link"
workaround stopped working.

**Fix.** Each area appears once:
`ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (`config.py`). The granted scope
for T. Rivera on 2026-09-19 (`ACTIVITY:WRITE,WELLNESS:READ`) has the same shape.

**Not verified against live Intervals.** The 400 body is a generic
`invalid_request`, and the log says it does not name the bad parameter. The
duplicate-scope cause is the best fit from the code and timing, plus the
external rule from the colleague's note. Confirm it with one real authorize
request before you rely on it.

## 3. Rivera's connection "expired" an hour after it was made (ticket #219)

**Cause.** Intervals returns no `refresh_token` and no `expires_in`. The server
filled in `DEFAULT_TOKEN_TTL = 3600`, so it treated the token as expiring after
an hour. The refresher then saw no refresh token and set status to
`expired, reconnect` (`logs/connect-attempt.log`, section 3). The token was
never expired. The app invented the expiry.

**Fix.**
- Removed the assumed TTL, `expires_at`, `refresh_token` handling and the
  `refresh_tokens()` thread. A connection stays `connected` until the athlete
  revokes it.
- Revocation is found lazily: when wellness gets a 401 from Intervals, the token
  is cleared and the status becomes `expired, reconnect`. The endpoint returns
  409, and the UI shows the Connect button again.

## What was changed

- `config.py`: deduplicated `SCOPES`; removed `REFRESH_INTERVAL`.
- `server.py`: `auth/init` moved to POST and returns JSON; removed the GET route;
  removed the TTL, expiry and refresh code; 401 from Intervals on wellness marks
  the connection as needing a reconnect.
- `static/app.js`: the link is now a button that POSTs and then navigates.

## Verification

Run in-process on port 8790 against a local fake Intervals server (`INTERVALS_BASE`
pointed at localhost; nothing external was contacted):

1. POST init without auth: 401
2. GET init (old link): 404
3. POST init with auth: 200 with `authorize_url`; scope is `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`
4. Callback with code and state: 302 to `/?connected=1`
5. Status after connect: connected, athlete `i1`
6. Wellness: 200
7. Wellness after the token is revoked: 409, and the log records "token revoked, reconnect"
8. Status after revoke: `expired, reconnect`
9. POST init again (reconnect): 200

`node --check static/app.js` and a parse of `server.py` both pass.

**Not tested:** a real Intervals.icu account, the real token endpoint's exact
behavior, and the live authorize screen.

## Things that need your attention

- **The server on port 8766 is still the old code.** Process 44757 (`python3
  server.py`, started 01:07) is running the pre-fix version. Restart it to pick up
  these changes. I did not stop it.
- **Token storage is still in memory and in plaintext.** Intervals tokens do not
  expire, so they are long-lived credentials. Encrypt them at rest before prod.
- **Token exchange still sends `grant_type` and `redirect_uri`.** The colleague's
  note says Intervals wants only `client_id`, `client_secret`, `code`. That did not
  match what we see: the 2026-09-19 exchange succeeded with the extra fields, so I
  left them out of the change.
- **Account-mismatch guard on reconnect is not implemented.** A reconnect overwrites
  the stored athlete without checking the id. Worth adding if athletes can log into
  a different Intervals account.
- **State signing already covers the colleague's concern.** `sign_state` is an
  HMAC with a 15-minute max age, so I did not switch to JWT. It has no `purpose`
  claim, which is a minor gap.
- **The colleague's note was used for:** the POST-init fix (point 4 of their
  note, which matched our 401 exactly), the no-refresh-token and "handle revocation
  lazily" rule, and the scope-dedup rule. Not used: the JWT state format and the
  athlete-id handling (already in place), and the exchange-field change (see above).
