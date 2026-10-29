# Intervals.icu connection failures

1. The Connect control was a normal link. Browser navigation does not include the bearer token held in `localStorage`, so `/api/intervals/auth/init` returned 401 even while the athlete was signed in. The button now calls that endpoint through the authenticated API wrapper, then navigates to the returned Intervals.icu URL.
2. The requested scopes included both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals.icu accepts one permission per area; WRITE already includes READ. This made the manually opened authorize URL fail with `invalid_request`. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. The token response had neither `expires_in` nor `refresh_token`, but the app assumed a one hour lifetime and then marked the connection expired. Intervals.icu's OAuth tokens do not use refresh tokens. The app now stores the access token without a made-up expiration or refresh pass; a real revocation or invalid token can still be reported by the API.

Local checks covered anonymous and authenticated auth initiation, the generated scopes, connection storage, and status. A live OAuth completion was not possible with the placeholder client credentials in this repository.

Provider reference: [Intervals.icu OAuth support](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759).
