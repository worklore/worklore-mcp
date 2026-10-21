# Intervals.icu connection failures

1. The Connect control was a normal link to `/api/intervals/auth/init`. A document navigation cannot send the SPA's `Authorization: Bearer` header, so the endpoint returned 401 for every athlete. The button now calls the endpoint through the authenticated `api()` wrapper, then navigates to the returned authorize URL.
2. The requested scope string included both READ and WRITE for ACTIVITY and CALENDAR. Intervals.icu treats WRITE as including READ for a resource; the redundant permissions made the authorize request invalid. The app's documented needs are wellness reads and calendar writes, so it now requests `WELLNESS:READ,CALENDAR:WRITE`.
3. Intervals.icu's token response has no `refresh_token` or `expires_in`. Its OAuth access tokens do not use the refresh-token expiry flow. The server invented a one-hour lifetime and then discarded a working token. It now retains the access token until disconnect or a provider rejection.

The local logs establish the missing header, invalid authorize request, and invented one-hour expiry. Intervals.icu's [OAuth documentation](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) documents scope semantics and the token response; its maintainer also states there are no refresh tokens.
