# Intervals.icu integration: root causes

1. **The Connect button lost the athlete's authentication.** The SPA used a normal link to `/api/intervals/auth/init`, but that endpoint requires the same `Authorization: Bearer` header as the other API calls. Browser link navigation does not use the SPA's authenticated `fetch` wrapper, so every click received `401 Unauthorized` before OAuth began. The button now calls the endpoint through the wrapper, and the endpoint returns the signed authorize URL for the browser to open.

2. **The authorize URL requested conflicting scopes.** It included both `READ` and `WRITE` for the same resources. Intervals.icu defines `WRITE` as including `READ`, so these redundant pairs are invalid and produce `invalid_request` before the consent screen. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **The server invented a one-hour token lifetime.** A normal Intervals.icu token response has an access token but no refresh token or `expires_in`. The server incorrectly supplied a 3,600-second default and then marked the connection expired when no refresh token was available. Tokens without an advertised expiry now have `expires_at = None` and are left connected; the refresh pass only considers tokens with an explicit expiry. Tokens with an explicit expiry but no refresh token are not marked expired early.

Reference: [Intervals.icu OAuth documentation](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759).
