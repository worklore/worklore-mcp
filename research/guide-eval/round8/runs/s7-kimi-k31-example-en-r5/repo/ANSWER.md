# Intervals.icu integration: causes and fixes

## Root causes

1. **The Connect button lost the athlete's authentication.** It was a full-page `GET` link, so the browser did not send the SPA's `Authorization: Bearer` header. The server therefore returned 401 before OAuth began, exactly as captured in `logs/connect-attempt.log`. Init is now an authenticated `POST` that returns `{authorize_url}`; the SPA opens that URL with `window.location.assign`.

2. **The authorize URL requested duplicate scope areas.** `ACTIVITY:READ,ACTIVITY:WRITE` and `CALENDAR:READ,CALENDAR:WRITE` each name the same area twice. Intervals.icu rejects that with `Duplicate scope` (surfacing as the logged 400 `invalid_request`), and `:WRITE` already includes read access. The scope is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.

3. **The app invented a one-hour token lifetime.** Intervals.icu returned neither `expires_in` nor `refresh_token`, but the app defaulted to 3,600 seconds and then cleared the valid token when it could not refresh it. This caused Rivera's unnecessary reconnect prompt. Intervals.icu tokens remain valid until revoked, so the artificial expiry and refresh worker are gone. If an API call actually returns 401, the app now clears the access token and reports `revoked, reconnect`.

## Other corrections

- The code exchange now sends only `client_id`, `client_secret`, and `code`, as Intervals.icu expects. The logs do not establish the old extra fields as a cause of the reported failures.
- OAuth state remains signed and limited to 15 minutes, and now also carries and validates an `intervals_oauth` purpose. The callback remains unauthenticated because it is a provider redirect.
- Reconnecting with a different Intervals.icu athlete is rejected without replacing the existing connection.

## Which parts of the colleague's note applied

- **Token lifetime and lazy revocation:** applied. Encryption at rest did not apply to this stdlib demo because connections are held only in memory, not persisted.
- **Duplicate scopes:** applied; one scope per area, with `:WRITE` where writing is required.
- **Standard-lite token exchange:** applied, including use of the returned athlete id and name.
- **POST init and SPA redirect:** applied; this was the direct cause of the Connect button's universal 401.
- **Signed, expiring state with purpose and the athlete-mismatch guard:** applied. The existing HMAC-signed state mechanism was retained rather than adding a JWT dependency.

## Verification

Python and JavaScript syntax checks passed. A local mock Intervals.icu provider exercised the complete HTTP flow: authenticated init, authorize URL validation, three-field code exchange, callback, connected status, wellness retrieval, provider 401/revocation handling, athlete-mismatch rejection, and successful same-athlete reconnect. No external service was contacted; a real-account OAuth check was not possible with the placeholder credentials and the prohibition on external submissions.
