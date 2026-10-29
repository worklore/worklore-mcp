# Causes

1. **Connect button always 401s (confirmed).** The button was a plain `<a href="/api/intervals/auth/init">`. A document navigation can't send the `Authorization: Bearer` header (the token lives in localStorage and is only added by the SPA's `fetch` wrapper), so `require_user()` rejected everyone. Fix: the button now calls `auth/init` through `api()` with `Accept: application/json`; the server returns `{url}` and the SPA navigates to it. (Plain callers still get the 302.)

2. **Intervals rejects the authorize URL with `400 invalid_request` (partly unverified).** Since the calendar sync (2026-10-02) the request asks for `ACTIVITY:READ,ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:READ,CALENDAR:WRITE`, and it also never sent `response_type=code`. Intervals' error body doesn't name the parameter, and I couldn't reach their OAuth docs, so I can't prove which one it minds. Changes: added `response_type=code`, and trimmed scopes to `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE` (Rivera's working token shows WRITE was granted without a separate READ, so the READ entries look redundant). **Please test against real Intervals**; if it still 400s, bisect by removing the calendar scope first.

3. **Connections "expire" after an hour (confirmed from log).** Intervals' token response has no `expires_in` and no `refresh_token`, i.e. the token is long-lived. `store_connection` invented a 3600s TTL (`DEFAULT_TOKEN_TTL`), and the refresher then marked the connection "expired, reconnect" because there was no refresh token. Fix: with no stated lifetime, `expires_at` is `None` and the refresher skips it; expiry/refresh only applies when the provider supplies `expires_in`.

Rivera should reconnect once after the fix (the stored connection is already expired).
Not tested end-to-end: no access to the real Intervals service.
