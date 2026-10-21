# Intervals.icu connection failure

Three causes compounded:

1. The Connect control was a normal link. A document navigation does not use the SPA's `fetch` wrapper, so it sent no `Authorization: Bearer` header. `/api/intervals/auth/init` therefore returned 401 for signed-in athletes. The button now calls that endpoint through the authenticated wrapper, then navigates to the returned authorization URL.
2. The OAuth request included both `ACTIVITY:READ` and `ACTIVITY:WRITE`, and both `CALENDAR:READ` and `CALENDAR:WRITE`. Intervals.icu specifies one access level per scope area; `WRITE` includes `READ`. The duplicated calendar scope caused the provider's `invalid_request` at authorization. The request now asks for `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. See the [Intervals.icu OAuth scope documentation](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) and a [reported duplicate-calendar-scope failure](https://forum.intervals.icu/t/domestique-a-free-open-source-science-based-cycling-training-app/130388?page=3).
3. The token response had neither `expires_in` nor `refresh_token`, but the app invented a 3600-second expiry and then marked the connection expired. Intervals.icu documents access tokens without a refresh flow. The app now keeps the access token until the athlete disconnects or reconnects; it no longer runs a refresh job. See the [provider's OAuth response and token discussion](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759).

The local tests cover authenticated initialization, the requested scopes and state, and storage of a token response without expiry fields. They use a local HTTP server and a mocked token exchange; no provider request is made.
