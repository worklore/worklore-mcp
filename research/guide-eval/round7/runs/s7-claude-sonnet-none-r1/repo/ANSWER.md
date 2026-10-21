# Intervals.icu connection: causes

1. **Connect button always 401s (everyone).** The button was a plain link to
   `/api/intervals/auth/init`. A browser navigation cannot send the
   `Authorization: Bearer` header (only the SPA's `fetch` wrapper does), so the
   server never saw the user and returned `{"error":"unauthorized"}`.
   Fix: `auth/init` now returns `{url}` as JSON; the button calls it through
   `api()` (with the header) and then sets `location.href` to that URL.

2. **Authorize step returns 400 `invalid_request` (the by-hand workaround broke).**
   The only change at that time was the calendar sync (2026-10-02) adding
   `CALENDAR:READ,CALENDAR:WRITE` to `SCOPES`. Removing state or changing
   redirect_uri did not change the error. Rivera's earlier grant was only
   `ACTIVITY:WRITE,WELLNESS:READ`, which suggests the client registration doesn't
   include calendar scopes. I could not verify this (no external calls made), so
   it is the most likely cause, not a confirmed one. Fix: default scopes are back
   to the previously working set; `INTERVALS_SCOPES` env var re-enables the
   calendar scopes once the client is allowed them at Intervals.icu. Calendar
   push will need that registration change.

3. **Connection "expired" after an hour.** Intervals' token response had no
   `expires_in` and no `refresh_token` (tokens last until revoked). The code
   assumed a 3600s default TTL, and with no refresh token the refresher marked the
   connection expired. Fix: expiry is only scheduled when the provider sends
   `expires_in`; otherwise the token is non-expiring. The refresher also no longer
   crashes on a refresh response lacking `expires_in`.

Not tested against the real Intervals.icu (not contacted).
