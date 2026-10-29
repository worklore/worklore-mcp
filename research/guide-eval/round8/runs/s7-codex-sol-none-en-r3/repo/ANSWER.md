# Intervals.icu connection failures

1. **Connect returned 401 before reaching Intervals.icu.** The SPA keeps its sign-in token in `localStorage` and adds it to `fetch` requests. Connect was a normal link to `/api/intervals/auth/init`; browser navigation did not include the `Authorization` header, so `require_user()` rejected it. The 2026-10-14 request in `logs/connect-attempt.log` shows this exact 401. Connect now calls an authenticated `POST` through the SPA's API wrapper, receives an authorize URL, and navigates to it.

2. **The authorize URL requested duplicate scope areas.** It included both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals.icu permits one entry per area; `WRITE` implies `READ`. This explains the provider's 400 before consent when the link was opened manually after calendar access was added. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **The app invented a one-hour token expiry.** Intervals.icu's token response has an access token but no `expires_in` or `refresh_token`. The refresher assigned a 3600-second default and then marked the connection expired about an hour later. The 2026-09-19 log shows the missing refresh token and the subsequent forced reconnect. Intervals.icu access tokens do not have that timed refresh flow. The app now retains the token and only asks for reconnection when the provider returns 401 on an API call.

The token exchange now sends the documented `client_id`, `client_secret`, and `code` form fields. Local tests cover initiation, scope uniqueness, callback storage without a refresh token, and reconnect on a rejected token. A live end-to-end consent flow was not run because this workspace has placeholder OAuth credentials.

Provider references: [OAuth support](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759), [token lifetime discussion](https://forum.intervals.icu/t/api-access-to-intervals-icu/609?page=36), [duplicate scope example](https://forum.intervals.icu/t/domestique-a-free-open-source-science-based-cycling-training-app/130388?page=3).
