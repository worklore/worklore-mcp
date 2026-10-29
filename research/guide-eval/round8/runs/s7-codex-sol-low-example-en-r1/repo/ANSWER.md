# Intervals.icu connection failure

The logs show three independent causes:

1. **Connect returned 401.** The SPA used a document-navigation link to `GET /api/intervals/auth/init`. Its sign-in token is sent only by the `fetch` wrapper, so that navigation had no `Authorization` header. The button now makes an authenticated `POST`, receives `{ "authorize_url": ... }`, and navigates to that URL.
2. **The authorize URL returned 400.** The configured scopes repeated `ACTIVITY` and `CALENDAR` with both `:READ` and `:WRITE`. Intervals rejects a repeated area; `:WRITE` includes read access. The scopes now list each area once: `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`. The log's generic `invalid_request` does not identify a parameter, so this cause is supported by the configured URL and the provider rule in the colleague's note, not by an explicit error message in that response.
3. **A working connection was marked expired after about an hour.** Rivera's token response had neither `expires_in` nor `refresh_token`. The server invented a 3600-second expiry and its refresh worker cleared the token. Intervals tokens remain usable until revoked, so the invented expiry and refresh worker are removed. An upstream 401 now clears the token and marks the connection for reconnect.

The callback still validates signed state before exchanging the code; it now also checks the state purpose, age, and user ID. The token exchange sends only `client_id`, `client_secret`, and `code`. A reconnect cannot replace an existing Intervals athlete with another athlete ID.

## Colleague's note

Applied: authenticated POST init with frontend navigation; one scope per area; no assumed token expiry or refresh; lazy revocation handling; callback state validation; minimal token exchange and athlete ID from the token response; account mismatch protection. The note's exact JWT state format was not adopted: this stdlib app already uses an HMAC-signed state, which now includes an OAuth purpose and a 15-minute age check. The note's encryption-at-rest recommendation remains a production storage requirement; this repository only has an in-memory connection store, so there is no durable token-at-rest implementation to change here. Its suggested live Intervals verification could not be performed with the placeholder OAuth credentials in `config.py`.
