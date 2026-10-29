# Intervals.icu connection: causes and fixes

Symptoms (from `logs/` and `logs/support-tickets.md`):

- **#214:** every athlete who clicks Connect lands on `{"error": "unauthorized"}`.
- **#219:** T. Rivera's connection was marked "expired, reconnect" about an hour after it was made, without any revoke on the Intervals side.
- Pasting the authorize link by hand also fails, with `invalid_request`, before any consent screen.

## Causes

### 1. The Connect button is a GET link, so the request has no auth header (#214)

`static/app.js` rendered `<a href="/api/intervals/auth/init">`. A full-page navigation does not send the SPA's `Authorization: Bearer` header, which only travels on `fetch`. `server.py` correctly returns 401 for it. `connect-attempt.log` section 1 shows exactly this: `GET /api/intervals/auth/init 401 (no Authorization header)`, with `Referer` set and the document-navigation request.

Fix: `auth/init` is now an authenticated **POST** that returns `{"authorize_url": ...}` as JSON. The button calls it with `fetch` and then does `window.location.assign(authorize_url)`.

### 2. The scope string lists the same area twice (blocks the authorize step)

`config.SCOPES` was `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`. Both `ACTIVITY` and `CALENDAR` appear twice, and `:WRITE` already implies `:READ`. The colleague's note says Intervals rejects this with `Duplicate scope`.

Fix: `SCOPES = "ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE"`. I kept `ACTIVITY:WRITE` and `WELLNESS:READ` (the app reads wellness and writes workouts to the calendar; nothing in the code reads activities). I did not add `SETTINGS:WRITE` from the note, since nothing uses it.

Caveat, not settled by the logs: the captured authorize failure body is the generic `{"error":"invalid_request"}`, not the text "Duplicate scope". The timeline also fits imperfectly. The calendar scopes were added on 2026-10-02, which matches when the failures started. But `ACTIVITY:READ,ACTIVITY:WRITE` was probably already in the config on 2026-09-19, when Rivera's pasted link succeeded. If that is right, the duplicate rule is narrower than the note says, or the old string was different. The git history has only a `base` commit, so I could not check. Removing the duplicates is correct under either reading, but only a real authorize request confirms it.

### 3. The app invented a 1-hour expiry for a token that never expires (#219)

Intervals' token response has no `expires_in` and no `refresh_token`. `store_connection` filled in `DEFAULT_TOKEN_TTL = 3600`, and the background `refresh_tokens` loop marked the connection `expired, reconnect` once it was within 5 minutes of that made-up deadline. Rivera's log shows connect at 17:41:04 and expiry at 18:37:12, which is that timer. Intervals had not revoked anything, as the ticket says.

Fix: removed `DEFAULT_TOKEN_TTL`, `expires_at`, `refresh_token`, the refresh loop, and its thread. A token is stored with no expiry. The app learns it has been revoked from a 401 on the next API call.

### 4. A revoked token was not cleared

`wellness()` passed the 401 through to the client but kept the dead token as `connected`, so the status card kept saying connected.

Fix: on a 401 from Intervals, `wellness()` sets the status to `revoked, reconnect` and clears the access token. The card shows the status and the Connect button. A reconnect replaces the stored record.

## What the colleague's note said, and what applied

| Note point | Applied? | Notes |
|---|---|---|
| 1. No `refresh_token`, no `expires_in`; handle revocation lazily on 401 | **Yes** | Cause 3 and fix 4. The note's "encrypt at rest" was not applied. Tokens are in an in-memory dict here, and the prod store is not in this repo. |
| 2. `Duplicate scope`: each area at most once, `:WRITE` implies `:READ` | **Yes** | Cause 2. Scopes chosen for what this app does, not the note's full list. The "Duplicate scope" text is unconfirmed (see caveat). |
| 3. Token exchange is "standard-lite"; athlete id comes back in the response | **Partly** | The athlete id was already taken from the response, so no extra "who am I" call. The exchange still sends `grant_type` and `redirect_uri`. Rivera's exchange succeeded with them on 2026-09-19, so they are accepted. I did not remove them. |
| 4. Init must be an authenticated POST, not a GET link; frontend uses `window.location.assign` | **Yes** | Cause 1 and exactly the case in `connect-attempt.log`. |
| `state` carries the identity: signed, 15-minute TTL, validated before exchange | **Already in place** | `sign_state`/`verify_state` already did this (HMAC, `max_age=900`). |
| `state` should carry a `purpose` claim | Not applied | Not a cause of any reported failure. Cheap to add if you want it. |
| Account-mismatch guard on reconnect | Not applied | Not a cause. It would reject a reconnect as a different athlete, which is a real product decision. |

## Verification

No real Intervals.icu account or client credentials were available, and the ground rules rule out reporting to the service. I used a local mock of Intervals (through the existing `INTERVALS_BASE` override) that models the behaviour in the logs and the note. It is not a substitute for a real check.

Results, before and after the change, against the mock:

- Navigation `GET /api/intervals/auth/init` with no header: 401 before, 404 after (the route is gone). The SPA uses the POST.
- Authorize with the old scope string: 400 `Duplicate scope` before (mock). With the new scope string: 302 to the callback.
- Connect, callback, status, and wellness: the old flow never reached the callback. The new flow connects, returns 200 for wellness, and stores no expiry field.
- Revoke at the mock, then wellness: before, status stayed `connected`. After, wellness returns 401 and status is `revoked, reconnect`.
- Reconnect after revocation: 302 to `/?connected=1`, status back to `connected`.
- `node --check static/app.js` and `py_compile` both pass.

I did not run the app on port 8766. A `server.py` process (PID 9025) was already listening there, and I left it alone.

## Still to check on a real account

1. Sign in as an athlete, click Connect, and confirm you reach Intervals' consent screen rather than an error page. This settles the `Duplicate scope` question.
2. After connecting, `GET /api/intervals/wellness` should return data.
3. Revoke tricoach in Intervals' settings, call wellness again, and confirm the card shows `revoked, reconnect` with a working Connect button.

## Noticed, not changed

- `static/app.js` falls back to `"tok-okafor"` when `localStorage` has no `tc_token`. In prod that means an unauthenticated browser acts as a real user. This is a dev convenience and should be removed before deploy.
- `config.py` holds a placeholder `APP_SECRET` and `CLIENT_SECRET`. The README says the real pair is in the deploy environment, so this is only a dev setup concern.
- No changes were committed.
