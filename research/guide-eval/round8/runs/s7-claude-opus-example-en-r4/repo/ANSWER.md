# Intervals.icu connection: causes and fix

There are three separate bugs. Fixing only the first one would still leave every athlete stuck.

## Causes

### 1. The Connect button was a plain link to an endpoint that needs authentication (everyone, ticket #214)
`static/app.js` rendered `<a href="/api/intervals/auth/init">`. That makes the browser load a new page, and a page load does not send the `Authorization: Bearer` header. The SPA only adds that header in its `fetch` wrapper, because the token lives in `localStorage`. `auth_init()` calls `require_user()`, so every click returned `401 {"error": "unauthorized"}`. `logs/connect-attempt.log` §1 shows this: `GET /api/intervals/auth/init 401 (no Authorization header)`, and the browser request carries no Authorization header.

**Fix:** `/api/intervals/auth/init` is now an authenticated **POST** that returns `{"authorize_url": ...}` as JSON. The button calls it through the `api()` wrapper and then runs `window.location.assign(authorize_url)`. The old GET route is gone. The callback still identifies the user from the HMAC-signed `state`, which expires after 15 minutes.

### 2. The scope list names the same area twice (authorize step returns 400, log §2)
`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. Intervals rejects a scope list that names the same area twice, because `:WRITE` already includes `:READ`. That matches the timeline: the problem started when calendar sync (2026-10-02) added `CALENDAR:READ,CALENDAR:WRITE`, and pasting the link stopped working too. Intervals' 400 response just says `invalid_request` without naming a parameter. So this cause comes from the evidence and the colleague's note, not from Intervals stating it. The log also shows that changing `state` or `redirect_uri` did not fix it, which rules those out.

**Fix:** `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`, with each area listed once. This keeps the same permissions as before. Rivera's grant already came back as `ACTIVITY:WRITE,WELLNESS:READ`.

### 3. Our server made up a 1-hour expiry for tokens that never expire (Rivera, ticket #219)
Intervals' token response has no `expires_in` and no `refresh_token`, and the token stays valid until the athlete revokes it. `store_connection()` filled in `DEFAULT_TOKEN_TTL = 3600`, and the background `refresh_tokens()` thread then found "no refresh token" and threw away a valid token: `token expiry passed and no refresh token on file -> expired, reconnect` (log §3). Rivera revoked nothing, and tricoach is still listed in their Intervals apps. Our server dropped the token by itself.

**Fix:** removed the made-up TTL, `expires_at`, `refresh_token`, the refresher thread and `REFRESH_INTERVAL`. Revocation is now detected when it happens: a 401 from Intervals on `/wellness` clears the stored token and sets the status to `revoked, reconnect`, so the UI shows the Connect button again.

Rivera's old token was already thrown away, so Rivera needs to connect once more. With fixes 1 and 2 the button now works.

## How it was checked
I ran `server.py` against a local fake Intervals server. It rejects scope lists that repeat an area with `invalid_request`, and it returns 401 after a revoke. Results:
- `GET /auth/init` returns 404.
- `POST /auth/init` without auth returns 401.
- `POST /auth/init` with auth returns an authorize URL with the new scopes.
- The authorize step redirects to the callback, which exchanges the code and redirects to `/?connected=1`.
- Status is `connected`, and `/wellness` returns data.
- After the revoke, `/wellness` returns 401 and status becomes `revoked, reconnect`.
- The old scope string gets `invalid_request` from the fake server.

I have not tested against the real intervals.icu. Note: other processes were already listening on ports 8766 and 8777 on this machine. I left them alone and tested on 18766/18799.

## Which parts of the colleague's note applied
- **#4 (init must be an authenticated POST returning `{authorize_url}`)**: applied. This is cause 1, with exactly the same symptom.
- **#2 ("Duplicate scope")**: applied. This is cause 2. Our 400 body is a generic `invalid_request` rather than the "Duplicate scope" text in the note, so the match rests on the timeline and the scope string. I used our own scope set, not the note's list; we don't need `SETTINGS:WRITE`.
- **#1 (no refresh_token or expiry; handle revocation on the first 401)**: applied. This is cause 3, and I added the clear-on-401 handling.
- **#3 (token exchange needs only `client_id`, `client_secret`, `code`; response includes `athlete`)**: the `athlete` part was already used. Our exchange also sends `grant_type` and `redirect_uri`, but Rivera's exchange succeeded with them, so they are not a cause. I left them unchanged.
- **State as a signed JWT with a `purpose` claim**: not needed. Our HMAC-signed state already includes the user id and a 15-minute TTL, and `APP_SECRET` signs nothing else.
- **Account-mismatch guard on reconnect, encrypting tokens at rest**: reasonable hardening, but not a cause of these failures. Not done here; storage in this repo is in memory. Prod should encrypt the token, since it never expires.
- **Registration and the "Reproduce/Verify" steps against real Intervals**: not done. They need real credentials and calls to an outside service.
