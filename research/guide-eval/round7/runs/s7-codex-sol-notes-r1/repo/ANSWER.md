# Intervals.icu connection failures

1. **Connect returned 401 for everyone.** The SPA used a normal link to `GET /api/intervals/auth/init`. A browser navigation does not include the Bearer token that the SPA's `fetch` wrapper reads from `localStorage`, so the authenticated endpoint rejected it. Connect now calls an authenticated `POST` with `fetch`, receives an `authorize_url`, and navigates to that URL.

2. **The hand-built authorization link failed before consent.** The requested scope included both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals treats `WRITE` as including `READ` and rejects duplicate areas. The scope is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **Rivera was told to reconnect after about an hour.** Intervals' token response had neither `expires_in` nor `refresh_token`. The server invented a 3600-second lifetime, then cleared the valid token on its next refresh pass. Intervals tokens remain valid until revoked, so the assumed expiry and refresh loop are removed. An Intervals API 401 now clears that token and shows a reconnect status.

4. **The code exchange used extra fields.** The server sent `grant_type` and `redirect_uri` along with the code. The Intervals token endpoint expects `client_id`, `client_secret`, and `code`; the exchange now sends those three fields.

Local tests cover authenticated init, scope construction, callback exchange, connection status without an expiry, revocation handling, and reconnect account matching. They use mocks and do not contact Intervals.icu. A live consent flow could not be verified without contacting the external service.
