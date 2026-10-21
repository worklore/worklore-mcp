# Intervals.icu connection failures

1. The Connect control was a full-page GET link to `/api/intervals/auth/init`. The app's login token lives in localStorage and is attached only by its fetch wrapper, so the navigation had no `Authorization` header and every click returned 401. Init is now an authenticated POST fetched by the SPA; it returns `authorize_url`, which the browser then opens.
2. The authorization URL requested `ACTIVITY:READ` and `ACTIVITY:WRITE` together, and likewise both calendar scopes. Intervals treats WRITE as including READ and rejects repeated areas with “Duplicate scope.” The scope is now `ACTIVITY:WRITE,WELLNESS:READ,CALENDAR:WRITE`.
3. The server assumed a one-hour expiry when the token response omitted `expires_in`, then its refresher marked the connection expired because there was no `refresh_token`. Intervals access tokens have neither field and remain valid until revoked. The expiry and refresh machinery are removed. A 401 from the Intervals API now clears the encrypted token and exposes a reconnect state.
4. The token exchange also sent `grant_type` and `redirect_uri` even though Intervals expects only `client_id`, `client_secret`, and `code`. It now sends exactly those fields and uses the returned `athlete.id`. The callback validates a signed, 15-minute JWT state with the app user id and purpose, and rejects a different athlete id on reconnect.

The real account flow and revocation check require configured OAuth credentials and an Intervals account; they cannot be completed from this local fixture.
