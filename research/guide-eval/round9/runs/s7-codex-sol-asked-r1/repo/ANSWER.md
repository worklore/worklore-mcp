# Intervals.icu connection failure

## Causes

1. **The Connect button lost the tricoach login header.** It was an `<a>` link to the authenticated `GET /api/intervals/auth/init` endpoint. Browser navigation does not send the `Authorization: Bearer` header that the SPA adds to `fetch` calls. The 401 in `logs/connect-attempt.log` is the result. The button now makes an authenticated `POST` through the SPA's API wrapper, then navigates to the returned `authorize_url`.

2. **The requested scopes contained duplicate areas.** `ACTIVITY:WRITE` already includes `ACTIVITY:READ`, and `CALENDAR:WRITE` includes `CALENDAR:READ`. Requesting each pair made Intervals reject the manually opened authorize URL with HTTP 400 before consent. The scope string now requests each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **The app invented a one-hour token lifetime.** Rivera's token response had neither `expires_in` nor `refresh_token`, but the app defaulted to 3600 seconds and its refresher marked the connection expired in the five-minute pre-expiry window. Intervals access tokens have no scheduled expiry or refresh flow; they remain usable until revoked. The app no longer schedules expiry or attempts refresh. It marks a connection for reconnection only when an Intervals API call returns 401. Other provider errors leave the connection intact.

4. **The token exchange sent fields Intervals does not require.** The old request included `grant_type` and `redirect_uri`. The exchange now sends only `client_id`, `client_secret`, and `code`, matching Intervals' token endpoint. This was a latent issue behind the earlier authorize failures; the captured successful exchange does not establish that these extra fields caused a failure.

The callback continues to use signed, time-limited `state` to identify the tricoach user without a browser auth header. It now checks the state's purpose and rejects an Intervals athlete ID that differs from an existing connection for that user.

## Verification

`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_intervals` passes four local tests covering the init request, scopes, callback and token response without expiry fields, account mismatch, and provider 401 behavior. No live Intervals consent or wellness request was made.
