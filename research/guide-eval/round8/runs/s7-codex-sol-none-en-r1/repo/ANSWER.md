# Intervals.icu connection failures

1. **Connect returned 401 before OAuth started.** The SPA used a plain link to `/api/intervals/auth/init`. Browser navigation did not include the Bearer token that the SPA's `fetch` wrapper adds, so `require_user()` rejected every click. The button now calls that endpoint through the authenticated wrapper, receives an authorize URL, and navigates to it.

2. **The authorize request used conflicting scopes.** It requested both `READ` and `WRITE` for `ACTIVITY` and `CALENDAR`. [Intervals.icu's OAuth guide](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) says to specify one access level per scope family and that `WRITE` includes `READ`. The request now uses `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. This explains the logged `invalid_request` at the authorize step; the provider's generic response did not identify the rejected parameter.

3. **A working connection was marked expired after an invented hour.** Rivera's token response had neither `expires_in` nor `refresh_token`, but the app assigned a 3,600-second expiry and then demanded reconnection. The [documented Intervals.icu token response](https://forum.intervals.icu/t/intervals-icu-oauth-support/2759) likewise omits both fields. The app now records no expiry when the provider gives none; the refresher skips such tokens. Tokens with an explicit expiry still follow the existing refresh or reconnect path.

Local verification: `python3 -m unittest -v test_intervals` and `node --check static/app.js` pass. The tests cover the authenticated authorize URL, the requested scopes, the callback, and a refresh pass two hours after a token response without expiry. The real provider flow cannot be exercised locally with the placeholder OAuth credentials in `config.py`.
