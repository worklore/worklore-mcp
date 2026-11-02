# Intervals.icu connection failure

The failures had three separate causes:

1. **Every Connect click returned 401.** The SPA used a normal link to `GET /api/intervals/auth/init`. A page navigation does not include the bearer token kept in `localStorage`, so the backend saw no `Authorization` header. Connect now sends an authenticated `POST` through the SPA's API wrapper, receives an `authorize_url`, and navigates to it.
2. **Manually opened authorize links returned 400.** The requested scope listed `ACTIVITY` and `CALENDAR` twice, with both `:READ` and `:WRITE`. Intervals.icu treats `:WRITE` as including read access and rejects duplicate areas. The scope now lists each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. **Rivera was told to reconnect after about an hour.** Intervals.icu's token response contained neither `expires_in` nor `refresh_token`. The backend invented a 3600 second expiry and then discarded the valid token. The artificial expiry and refresh worker are gone. A connection stays active until an Intervals API call returns 401, at which point its token is cleared and the status prompts reconnection.

The callback also sent `grant_type` and `redirect_uri` in the token request. Intervals.icu expects only `client_id`, `client_secret`, and `code`; the exchange now sends those fields. Callback state remains signed and short lived, and reconnecting cannot silently switch a tricoach user to a different Intervals athlete.

Verification: `python3 -m unittest -v test_integration.py` passes local HTTP tests for initiation, callback and token exchange fields, connection beyond an hour, revocation, account mismatch, and state validation. No live Intervals.icu account was used in this workspace.
