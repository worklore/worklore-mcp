# Why Intervals.icu connect fails

1. **Connect button gets 401 for everyone.** It was a plain `<a href="/api/intervals/auth/init">`. A browser navigation can't send the `Authorization: Bearer` header (the token lives in localStorage and is only added by the SPA's `fetch` wrapper), so the server answered `{"error":"unauthorized"}`. Fix: the button now calls `auth/init` via `api()`, the endpoint returns `{"url": ...}`, and the SPA navigates to it.

2. **Authorize URL rejected with 400 `invalid_request` since the calendar sync (2026-10-02).** The only thing that changed is `SCOPES`, which gained `CALENDAR:READ,CALENDAR:WRITE` on top of redundant `ACTIVITY:READ` + `ACTIVITY:WRITE`. The scope string is the likely culprit (the format that worked for Rivera was `ACTIVITY:WRITE,WELLNESS:READ`, where a WRITE scope stands alone). I trimmed it to `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. **Unverified:** I can't call Intervals.icu from here, and its error body doesn't name the bad parameter. If it still 400s, test scope sets against the authorize URL one at a time.

3. **"Reconnect after an hour".** Intervals.icu's token response has no `expires_in` and no `refresh_token` (see Rivera's logged response); its tokens are long-lived. `store_connection` invented a 3600s TTL (`DEFAULT_TOKEN_TTL`), and the refresher then marked the connection expired because there was no refresh token. Fix: no `expires_in` means no expiry (`expires_at=None`), and the refresher skips such connections. The refresh path also no longer crashes on a response lacking `expires_in`.

Not tested end to end against the real Intervals.icu.
