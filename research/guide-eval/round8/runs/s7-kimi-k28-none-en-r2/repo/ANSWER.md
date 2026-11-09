# Why athletes couldn't connect Intervals.icu

Three independent defects, one per symptom. All fixed and verified end-to-end
against a local stand-in for Intervals.icu (via the `INTERVALS_BASE` override).

## 1. The Connect button never sent the athlete's credentials → 401 for everyone

The SPA's "Connect Intervals.icu" control was a plain link:
`<a href="/api/intervals/auth/init">`. The athlete's sign-in token travels
only as an `Authorization: Bearer` header added by the SPA's fetch wrapper —
browsers do **not** attach it to regular link navigations. So every click hit
`auth_init` with no header and got `401 {"error": "unauthorized"}`, even
though the athlete was signed in (confirmed by the dev-tools capture in
`logs/connect-attempt.log`, which shows an `Accept: text/html` document
navigation with no `Authorization` header).

This is also why Rivera's "reconnect" attempt failed the same way, and why
support's paste-the-link workaround had to use curl with a hand-added header.

**Fix:** `auth_init` now returns the authorize URL as JSON to an
authenticated fetch (`server.py`), and the SPA requests it through the
`api()` wrapper and then navigates to the returned URL
(`static/app.js`). Note the endpoint contract changed: it answers
`200 {"url": ...}` instead of `302` — the curl-based manual flow is now
`curl -s -H "Authorization: Bearer <token>" .../auth/init` and open `url`.

## 2. The authorize URL omitted `response_type=code` → 400 invalid_request

`auth_init` built the authorize URL with `client_id`, `redirect_uri`,
`scope`, `state` — but never `response_type`, which RFC 6749 §4.1.1 makes
mandatory. Intervals.icu used to tolerate the omission (the September
connection went through with this same code), then started enforcing it, so
every authorize request began dying with
`400 {"error":"invalid_request"}` before the consent screen. The bare error
body doesn't name the bad parameter — the two parameters support happened to
tweak (`state`, `redirect_uri`) were never the problem.

The calendar scopes in the support ticket are a red herring:
`CALENDAR:READ`/`CALENDAR:WRITE` are valid Intervals.icu scopes (their OAuth
docs list ACTIVITY, WELLNESS, CALENDAR, CHATS, LIBRARY, SETTINGS with
READ/WRITE suffixes), and the calendar sync merely shipped at the same time
the provider tightened validation.

**Fix:** `auth_init` now sends `response_type=code`
(`server.py`). Verified: the old URL shape is rejected with 400, the new one
reaches the consent redirect.

## 3. Intervals.icu tokens don't expire — the server killed them after an hour anyway

Intervals.icu's token response carries **no `expires_in` and no
`refresh_token`** (that is its documented response shape, and it matches
Rivera's exchange in `logs/connect-attempt.log` exactly). The server assumed
generic OAuth semantics: it substituted a made-up 1-hour TTL, and when that
hour passed with no refresh token to renew it, the background pass marked the
connection `"expired, reconnect"` and wiped the access token. That's the
"token expiry passed and no refresh token on file" line, ~56 minutes after
Rivera connected — and with the Connect button broken (cause 1), reconnecting
was impossible.

**Fix:** `store_connection`/`refresh_due` (`server.py`) — when the provider
doesn't say `expires_in`, the token is stored as non-expiring (`expires_at =
None`) and the refresher leaves it alone. If a provider *does* send
`expires_in`, behavior is unchanged: renew via `refresh_token` when one was
issued, otherwise mark expired when due.

## Verification (offline, against a local mock of Intervals.icu)

- `auth/init` with the Bearer header → 200 JSON; URL with `response_type=code`
  → provider 302 to callback with `code`+`state` → token exchange → 302 to
  `/?connected=1`; `status` → `connected`; `wellness` → data (for both
  `tok-okafor` and `tok-rivera`).
- Same URL minus `response_type=code` → 400 `invalid_request` (reproduces the
  October failure).
- Refresher pass simulated two hours after connect: Intervals-shaped
  connection (no `expires_in`, no `refresh_token`) stays `connected`;
  `expires_in`-bearing connections still expire or refresh as before.
