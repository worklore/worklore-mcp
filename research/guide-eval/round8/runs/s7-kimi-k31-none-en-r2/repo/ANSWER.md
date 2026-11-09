# Intervals.icu integration: root causes

## 1. The Connect button did not authenticate the athlete

The button was a normal link to `/api/intervals/auth/init`. Browser link navigation does not include the SPA's `Authorization: Bearer ...` header; that header is added only by the JavaScript `fetch` wrapper. The endpoint therefore returned 401 before creating an authorize URL, as shown in `logs/connect-attempt.log`.

The button now uses an authenticated POST to obtain the authorize URL as JSON, then navigates to that URL. The authenticated GET endpoint still redirects for compatibility.

## 2. The authorize request contained conflicting scopes

The scope list requested both `READ` and `WRITE` for activities and the calendar. Intervals.icu defines `WRITE` as including `READ`, so these pairs are redundant and the provider rejected the request with `invalid_request` before showing consent. This appeared when calendar access was added.

The request is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`, preserving the required access without duplicate permissions. See the [Intervals.icu OAuth scope documentation](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759).

## 3. Non-expiring tokens were treated as one-hour tokens

Intervals.icu access tokens do not expire and its OAuth flow does not issue refresh tokens. The token response in `logs/connect-attempt.log` is therefore normal: it has neither `expires_in` nor `refresh_token`.

The server incorrectly invented a 3600-second lifetime when `expires_in` was absent, then marked the connection `expired, reconnect` because it had no refresh token. It now stores `expires_at = None` when the provider omits `expires_in` and excludes that connection from expiry/refresh processing. See the [token lifetime discussion](https://forum.intervals.icu/t/api-access-to-intervals-icu/609?page=36).
