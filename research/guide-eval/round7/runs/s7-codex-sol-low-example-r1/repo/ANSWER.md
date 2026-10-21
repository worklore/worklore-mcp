# Intervals.icu connection failure

The Connect control was a document link to `GET /api/intervals/auth/init`. Browser navigation did not include the SPA's `Authorization` header, so the authenticated endpoint returned 401 for every athlete. The control now makes an authenticated `POST`, receives an authorize URL, and navigates to it.

The authorize URL also listed `ACTIVITY` and `CALENDAR` twice, once with `READ` and once with `WRITE`. Intervals rejects duplicate scope areas before consent. The scope is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`; write access includes read access for those areas.

Rivera's successful token response contained neither `expires_in` nor `refresh_token`. The server assumed a one-hour lifetime, then its refresher marked the connection expired despite no revocation. The false expiry and refresh loop are removed. The wellness proxy now marks a connection for reconnection only if Intervals returns 401. The token exchange now sends only `client_id`, `client_secret`, and `code`.

The colleague's note applied to the POST init flow, duplicate scopes, the absence of token expiry and refresh, the token exchange fields, and handling revocation on 401. The callback already used a signed, time-limited state rather than a JWT; it now also binds a purpose, rejects future timestamps, verifies the user exists, and prevents reconnecting a different Intervals athlete. The JWT format in the note was not required here. Its encryption-at-rest advice applies to production persistent storage, but this repository's connection store is memory only and has no at-rest token store to change. A live OAuth check requires the deployed client credentials and a real Intervals account, so it was not performed here.
