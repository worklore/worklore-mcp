# Intervals.icu connection failure

The logs show three independent causes:

1. The Connect control was a normal link to `GET /api/intervals/auth/init`. Browser navigation did not include the SPA's `Authorization` header, so the endpoint returned 401 for every athlete. It is now a button that makes an authenticated `POST` request, receives `authorize_url` as JSON, and navigates to that URL.
2. The authorize URL requested both `:READ` and `:WRITE` for ACTIVITY and CALENDAR. Intervals rejects repeated areas as a duplicate scope, preventing consent even when the init endpoint is bypassed. The scopes are now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. The token response for Rivera had neither `expires_in` nor `refresh_token`. The app invented a one-hour expiry and its background job then cleared a working token. The app now keeps the token until the athlete disconnects or an Intervals API request returns 401; that 401 marks the connection for reconnection.

The token exchange also sent `grant_type` and `redirect_uri`, which the colleague's note says this endpoint does not require. It now sends only `client_id`, `client_secret`, and `code`. The logs do not prove those extra fields caused a failed exchange, since Rivera's earlier exchange succeeded; this change aligns the request with the documented behavior in the note.

## Colleague's note

Applied: authenticated POST init with SPA navigation; one scope per area; the three-field code exchange; use of the returned `athlete.id`; no invented token expiry or refresh; lazy revocation handling on API 401; callback identity from a signed, time-limited state; and an account-mismatch check on reconnection.

Adapted: the existing state was already HMAC signed, so it was strengthened with a purpose and 15-minute expiry rather than replaced with a JWT. The callback remains an unauthenticated GET, as required by the redirect flow.

Not applicable here: encryption at rest, because this repository stores connections only in memory. Production persistence should encrypt these long-lived credentials. Live consent and revocation checks against Intervals were not run because this workspace has placeholder OAuth credentials and the task prohibits external service calls.

## Verification

`python3 -m unittest -v test_intervals` passes. The local HTTP test covers authenticated init, scope URL, callback and token request fields, connected status, wellness access, provider 401 reconnection, state validation, and account mismatch. It uses mocked provider responses and makes no external requests.
