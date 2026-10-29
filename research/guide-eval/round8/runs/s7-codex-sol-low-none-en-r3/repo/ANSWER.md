# Intervals.icu connection failures

1. **Connect returned 401.** The SPA used a normal link to `/api/intervals/auth/init`. Browser navigation does not carry the `Authorization` header that the SPA's `fetch` wrapper adds, so the endpoint rejected every click. Connect now calls the endpoint through the authenticated wrapper and navigates to the returned authorize URL.
2. **The authorize URL returned 400.** The requested scopes repeated `ACTIVITY` and `CALENDAR` as both `READ` and `WRITE`. Intervals.icu accepts one entry per resource; `WRITE` already grants read access. The scope list now requests `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. **The successful connection was discarded after about an hour.** Intervals.icu's token response contains an access token without `expires_in` or a refresh token. The code invented a 3600-second expiry, then marked the connection expired when no refresh token existed. It now keeps the access token until disconnect and no longer runs a refresh loop for these tokens. Provider API errors still surface to the caller.

Verified locally: authenticated initiation returns an authorize URL with unique scopes and valid state; unauthenticated initiation still returns 401; a stored Intervals token remains connected without synthetic expiry fields. Live authorization could not be exercised with the placeholder OAuth credentials in this repository.

Provider contract: [Intervals.icu OAuth documentation](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759).
