# Intervals.icu connection failures

1. The Connect link navigated to `GET /api/intervals/auth/init`. A document navigation does not carry the SPA's `Authorization` header, so every click returned 401. The button now makes an authenticated POST and navigates to the returned `authorize_url`.
2. The requested scopes repeated `ACTIVITY` and `CALENDAR` with both READ and WRITE. Intervals.icu rejects duplicate areas; WRITE already includes READ. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. The token response has neither `expires_in` nor `refresh_token`: Intervals.icu access tokens persist until revoked. Our one-hour fallback and refresher marked Rivera's valid connection expired. Both are removed. A 401 from the Intervals API now clears the credential and prompts reconnection.
4. The token exchange sent extra OAuth fields. It now sends only `client_id`, `client_secret`, and `code`. The callback validates a signed 15-minute state JWT and rejects an athlete ID mismatch on reconnection. Tokens are encrypted before storage.

Live consent and revocation checks require a registered Intervals.icu OAuth client and an athlete account; the repository has placeholder credentials.
